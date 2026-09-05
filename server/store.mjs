import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
const directory = path.resolve("server/data");
const file = path.join(directory, "store.json");
const seed = { currentPatientId: "P001", patients: [{ id: "P001", name: "演示患者" }], assignments: [], drafts: [], submissions: [] };
let writeQueue = Promise.resolve();
export async function readStore() { await mkdir(directory, { recursive: true }); try { return JSON.parse(await readFile(file, "utf8")); } catch (error) { if (error.code !== "ENOENT") throw error; await writeStore(seed); return structuredClone(seed); } }
export function writeStore(data) { writeQueue = writeQueue.then(async () => { await mkdir(directory, { recursive: true }); const temporary = `${file}.tmp`; await writeFile(temporary, `${JSON.stringify(data, null, 2)}\n`, "utf8"); await rename(temporary, file); }); return writeQueue; }
export async function resetStore() { await writeStore(structuredClone(seed)); }
