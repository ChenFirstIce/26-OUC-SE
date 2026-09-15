from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from test_flow import app, auth, valid_answers


def new_assignment(client, doctor, **extra):
    patient = client.post('/api/v1/patients', headers=doctor, json={
        'patient_code': 'I' + uuid4().hex[:10], 'full_name': '集成测试虚拟患者',
    })
    assert patient.status_code == 201, patient.text
    templates = client.get('/api/v1/questionnaires', headers=doctor).json()
    version = next(row['latest_version_id'] for row in templates if row['code'] == 'SCD_QUESTIONNAIRE')
    assignment = client.post('/api/v1/assignments', headers=doctor, json={
        'patient_id': patient.json()['id'], 'questionnaire_version_ids': [version],
        'title': '集成验证任务', **extra,
    })
    assert assignment.status_code == 201, assignment.text
    return assignment.json()


def enter(client, assignment):
    response = client.post('/api/v1/patient-session/verify', json={
        'token': assignment['token'], 'access_code': assignment['access_code'],
    })
    assert response.status_code == 200, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_draft_restore_conflict_submission_lock_and_history_scope():
    with TestClient(app) as client:
        doctor = auth(client, 'doctor1', 'Doctor123!')
        first = new_assignment(client, doctor)
        second = new_assignment(client, doctor)
        patient = enter(client, first)
        item_id = first['items'][0]['id']
        base = f'/api/v1/patient-session/tasks/{item_id}'
        task = client.get(base, headers=patient).json()
        answers = valid_answers(task['schema'])
        incomplete = client.post(base + '/submit', headers={**patient, 'Idempotency-Key': uuid4().hex}, json={'answers': {}, 'revision': 0})
        assert incomplete.status_code == 422
        saved = client.put(base + '/draft', headers=patient, json={'answers': answers, 'revision': 0})
        assert saved.status_code == 200
        restored = client.get(base, headers=patient).json()
        assert restored['answers'] == answers and restored['revision'] == 1
        assert client.put(base + '/draft', headers=patient, json={'answers': {}, 'revision': 0}).status_code == 409
        assert client.post(base + '/submit', headers={**patient, 'Idempotency-Key': uuid4().hex}, json={'answers': answers, 'revision': 0}).status_code == 409
        headers = {**patient, 'Idempotency-Key': uuid4().hex}
        result = client.post(base + '/submit', headers=headers, json={'answers': answers, 'revision': 1})
        assert result.status_code == 200, result.text
        repeat = client.post(base + '/submit', headers=headers, json={'answers': answers, 'revision': 1})
        assert repeat.status_code == 200 and repeat.json()['id'] == result.json()['id']
        assert client.put(base + '/draft', headers=patient, json={'answers': {}, 'revision': 2}).status_code == 409
        assert client.post(base + '/submit', headers={**patient, 'Idempotency-Key': uuid4().hex}, json={'answers': answers, 'revision': 2}).status_code == 409
        tasks = client.get('/api/v1/patient-session/tasks', headers=patient).json()
        assert [row['id'] for row in tasks['items']] == [item_id]
        assert tasks['items'][0]['submitted_at'] and tasks['items'][0]['duration_seconds'] >= 1
        assert 'total_score' not in tasks['items'][0]
        foreign = second['items'][0]['id']
        assert client.get(f'/api/v1/patient-session/tasks/{foreign}', headers=patient).status_code == 404
        report = client.get(f"/api/v1/assignments/{first['id']}/items/{item_id}/result", headers=doctor)
        assert report.status_code == 200


def test_direct_submission_without_opening_task():
    from app.core.database import SessionLocal
    from app.models import AssignmentItem
    with TestClient(app) as client:
        doctor = auth(client, 'doctor1', 'Doctor123!')
        assignment = new_assignment(client, doctor)
        patient = enter(client, assignment)
        item_id = assignment['items'][0]['id']
        with SessionLocal() as db:
            answers = valid_answers(db.get(AssignmentItem, item_id).questionnaire_version.schema_json)
        result = client.post(f'/api/v1/patient-session/tasks/{item_id}/submit', headers={**patient, 'Idempotency-Key': uuid4().hex}, json={'answers': answers, 'revision': 0})
        assert result.status_code == 200, result.text


def test_revoked_and_expired_packages_block_existing_sessions():
    with TestClient(app) as client:
        doctor = auth(client, 'doctor1', 'Doctor123!')
        for mode in ['revoked', 'expired']:
            assignment = new_assignment(client, doctor)
            patient = enter(client, assignment)
            if mode == 'revoked':
                assert client.post(f"/api/v1/assignments/{assignment['id']}/revoke", headers=doctor).status_code == 200
            else:
                changed = client.patch(f"/api/v1/assignments/{assignment['id']}", headers=doctor, json={'deadline': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()})
                assert changed.status_code == 200
            assert client.get('/api/v1/patient-session/tasks', headers=patient).status_code == 410
            assert client.post('/api/v1/patient-session/verify', json={'token': assignment['token'], 'access_code': assignment['access_code']}).status_code == 410


@pytest.mark.parametrize('code,answer,expected', [
    ('OUC_SCD_Q9', 'no', 0), ('OUC_SCD_Q9', 'yes', 9),
    ('OUC_ESS', 0, 0), ('OUC_ESS', 3, 24),
    ('OUC_EDINBURGH', 'left', -100), ('OUC_EDINBURGH', 'both', 0), ('OUC_EDINBURGH', 'right', 100),
])
def test_scale_boundaries(code, answer, expected):
    from app.services.scale_catalog import catalog_items
    from app.services.questionnaire import all_questions
    from app.services.scoring import score_questionnaire
    scale = next(item for item in catalog_items() if item['code'] == code)
    answers = {q['key']: answer for q in all_questions(scale['questionnaire_schema'])}
    if code == 'OUC_SCD_Q9':
        for key in ['scd_4', 'scd_5', 'scd_7']:
            answers[key] = 'often' if answer == 'yes' else 'never'
    assert score_questionnaire(scale['questionnaire_schema'], scale['scoring_json'], answers)[0] == expected


def test_gds_forward_and_reverse_boundaries():
    from app.services.scale_catalog import catalog_items
    from app.services.scoring import score_questionnaire
    scale = next(item for item in catalog_items() if item['code'] == 'OUC_GDS_15')
    reverse = {1, 5, 7, 11, 13}
    high = {f'gds_{i}': 'no' if i in reverse else 'yes' for i in range(1, 16)}
    low = {key: 'no' if value == 'yes' else 'yes' for key, value in high.items()}
    assert score_questionnaire(scale['questionnaire_schema'], scale['scoring_json'], high)[0] == 15
    assert score_questionnaire(scale['questionnaire_schema'], scale['scoring_json'], low)[0] == 0
