import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ResultCard from "./ResultCard";

const MOCK_RESULT = {
  post: {
    text: "The Ralph Wiggum technique is amazing for AI agents",
    author: "user.bsky.social",
    image_url: null,
  },
  bullets: [
    "Ralph Wiggum technique é um método de loop em bash para agentes de IA",
    "Foi criado por Geoffrey Huntley em meados de 2025",
    "Gerou o token $RALPH na blockchain Solana",
  ],
  sources: [
    "https://example.com/ralph",
    "https://ghuntley.com/ralph",
  ],
};

describe("ResultCard", () => {
  it("exibe o texto original do post", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    expect(screen.getByText(/Ralph Wiggum technique is amazing/i)).toBeInTheDocument();
  });

  it("exibe o autor do post", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    expect(screen.getByText(/user\.bsky\.social/i)).toBeInTheDocument();
  });

  it("exibe todos os bullets", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    MOCK_RESULT.bullets.forEach((bullet) => {
      expect(screen.getByText(bullet)).toBeInTheDocument();
    });
  });

  it("exibe os links das fontes", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(MOCK_RESULT.sources.length);
  });

  it("links das fontes apontam para as URLs corretas", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    MOCK_RESULT.sources.forEach((source) => {
      expect(screen.getByRole("link", { name: new RegExp(source) })).toHaveAttribute(
        "href",
        source
      );
    });
  });

  it("links abrem em nova aba", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    const links = screen.getAllByRole("link");
    links.forEach((link) => {
      expect(link).toHaveAttribute("target", "_blank");
    });
  });

  it("não exibe imagem quando image_url é null", () => {
    render(<ResultCard result={MOCK_RESULT} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("exibe imagem quando image_url está presente", () => {
    const resultComImagem = {
      ...MOCK_RESULT,
      post: { ...MOCK_RESULT.post, image_url: "https://cdn.bsky.app/img/abc.jpg" },
    };
    render(<ResultCard result={resultComImagem} />);
    expect(screen.getByRole("img")).toBeInTheDocument();
    expect(screen.getByRole("img")).toHaveAttribute("src", "https://cdn.bsky.app/img/abc.jpg");
  });
});
