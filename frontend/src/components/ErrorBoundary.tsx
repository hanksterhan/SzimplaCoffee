import { Component, type ReactNode, type ErrorInfo } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center space-y-4">
          <div className="text-5xl">☕</div>
          <h2 className="text-xl font-semibold">Something went wrong</h2>
          <p className="text-muted-foreground max-w-sm">
            An unexpected error occurred. Try refreshing or clicking retry below.
          </p>
          {import.meta.env.DEV && this.state.error && (
            <details className="text-left max-w-lg w-full">
              <summary className="cursor-pointer text-sm text-muted-foreground hover:underline">
                Error details (dev mode)
              </summary>
              <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto text-red-600 whitespace-pre-wrap">
                {this.state.error.message}
                {"\n\n"}
                {this.state.error.stack}
              </pre>
            </details>
          )}
          <Button onClick={this.handleRetry} variant="outline">
            ↺ Retry
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
