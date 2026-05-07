import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import LoadingState from "./LoadingState";

describe("LoadingState", () => {
  it("renderiza o skeleton de loading", () => {
    render(<LoadingState />);
    expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
  });

  it("exibe mensagem de status para o usuário", () => {
    render(<LoadingState />);
    expect(screen.getByText(/buscando contexto/i)).toBeInTheDocument();
  });

  it("exibe múltiplas linhas de skeleton", () => {
    render(<LoadingState />);
    const skeletonLines = screen.getAllByTestId(/skeleton-line/i);
    expect(skeletonLines.length).toBeGreaterThanOrEqual(3);
  });

  it("tem atributo aria-busy para acessibilidade", () => {
    render(<LoadingState />);
    expect(screen.getByTestId("loading-skeleton")).toHaveAttribute("aria-busy", "true");
  });
});
