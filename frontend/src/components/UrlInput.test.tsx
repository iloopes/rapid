import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import UrlInput from "./UrlInput";

const VALID_URL = "https://bsky.app/profile/user.bsky.social/post/abc123";

describe("UrlInput", () => {
  it("renderiza o campo de input", () => {
    render(<UrlInput onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByPlaceholderText(/cole a url/i)).toBeInTheDocument();
  });

  it("renderiza o botão de submit", () => {
    render(<UrlInput onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: /explain/i })).toBeInTheDocument();
  });

  it("chama onSubmit com a URL ao clicar no botão", () => {
    const onSubmit = vi.fn();
    render(<UrlInput onSubmit={onSubmit} isLoading={false} />);

    fireEvent.change(screen.getByPlaceholderText(/cole a url/i), {
      target: { value: VALID_URL },
    });
    fireEvent.click(screen.getByRole("button", { name: /explain/i }));

    expect(onSubmit).toHaveBeenCalledWith(VALID_URL);
  });

  it("chama onSubmit ao pressionar Enter", () => {
    const onSubmit = vi.fn();
    render(<UrlInput onSubmit={onSubmit} isLoading={false} />);

    const input = screen.getByPlaceholderText(/cole a url/i);
    fireEvent.change(input, { target: { value: VALID_URL } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSubmit).toHaveBeenCalledWith(VALID_URL);
  });

  it("não chama onSubmit com input vazio", () => {
    const onSubmit = vi.fn();
    render(<UrlInput onSubmit={onSubmit} isLoading={false} />);

    fireEvent.click(screen.getByRole("button", { name: /explain/i }));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("desabilita o botão quando isLoading é true", () => {
    render(<UrlInput onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("button", { name: /explain/i })).toBeDisabled();
  });

  it("desabilita o input quando isLoading é true", () => {
    render(<UrlInput onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByPlaceholderText(/cole a url/i)).toBeDisabled();
  });

  it("exibe erro para URL de domínio inválido", () => {
    const onSubmit = vi.fn();
    render(<UrlInput onSubmit={onSubmit} isLoading={false} />);

    fireEvent.change(screen.getByPlaceholderText(/cole a url/i), {
      target: { value: "https://twitter.com/user/status/123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /explain/i }));

    expect(screen.getByText(/url inválida/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
