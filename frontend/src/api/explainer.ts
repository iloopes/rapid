export interface PostInfo {
  text: string;
  author: string;
  image_url: string | null;
}

export interface ExplainResult {
  post: PostInfo;
  bullets: string[];
  sources: string[];
}

export async function explainPost(url: string): Promise<ExplainResult> {
  const response = await fetch("/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail ?? "Erro ao processar o post");
  }

  return data as ExplainResult;
}
