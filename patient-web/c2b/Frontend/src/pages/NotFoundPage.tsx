import { SearchX } from "lucide-react";
import { Link } from "react-router-dom";
import { EmptyState } from "../components/ui";

export function NotFoundPage() {
  return <EmptyState icon={<SearchX />} title="找不到这个页面">请检查地址，或<Link to="/">返回功能首页</Link>。</EmptyState>;
}
