import { Component, type ReactNode, type ErrorInfo } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

function isNetworkError(err: Error): boolean {
  return (
    err.message.toLowerCase().includes("network") ||
    err.message.toLowerCase().includes("failed to fetch") ||
    err.message.toLowerCase().includes("load failed")
  );
}

export class QueryErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[QueryErrorBoundary]", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      const err = this.state.error;
      const isNetwork = err ? isNetworkError(err) : false;

      return (
        <div className="flex flex-col items-center justify-center min-h-[200px] p-6 text-center space-y-3 rounded-lg border border-dashed">
          <div className="text-3xl">{isNetwork ? "📡" : "⚠️"}</div>
          <h3 className="font-semibold">
            {isNetwork ? "Connection problem" : "Failed to load data"}
          </h3>
          <p className="text-sm text-muted-foreground max-w-xs">
            {isNetwork
              ? "Check your network connection and try again."
              : "The server returned an error. Please try again in a moment."}
          </p>
          {import.meta.env.DEV && err && (
            <p className="text-xs text-red-500 font-mono max-w-sm truncate">
              {err.message}
            </p>
          )}
          <Button size="sm" variant="outline" onClick={this.handleRetry}>
            ↺ Retry
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
