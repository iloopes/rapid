import { describe, it, expect, vi, beforeEach } from "vitest";
import { explainPost } from "./explainer";

const VALID_URL = "https://bsky.app/profile/user.bsky.social/post/abc123";

const MOCK_RESPONSE = {
  post: { text: "Ralph Wiggum technique", author: "user.bsky.social", image_url: null },
  bullets: ["Bullet 1", "Bullet 2", "Bullet 3"],
  sources: ["https://example.com"],
};

describe("explainPost API", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("chama o endpoint correto", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_RESPONSE,
    });

    await explainPost(VALID_URL);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/explain"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("envia a URL no body da requisição", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_RESPONSE,
    });

    await explainPost(VALID_URL);

    const callBody = JSON.parse((fetch as any).mock.calls[0][1].body);
    expect(callBody.url).toBe(VALID_URL);
  });

  it("retorna bullets e sources quando sucesso", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_RESPONSE,
    });

    const result = await explainPost(VALID_URL);

    expect(result.bullets).toHaveLength(3);
    expect(result.sources).toHaveLength(1);
  });

  it("lança erro quando response não é ok", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: "URL inválida" }),
    });

    await expect(explainPost("url-invalida")).rejects.toThrow(/URL inválida/i);
  });

  it("lança erro quando servidor retorna 500", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Erro interno" }),
    });

    await expect(explainPost(VALID_URL)).rejects.toThrow();
  });

  it("lança erro quando há falha de rede", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    await expect(explainPost(VALID_URL)).rejects.toThrow(/Network error/i);
  });
});
