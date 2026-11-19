import React from "react";
import { RotateCcw, TriangleAlert } from "lucide-react";

// Keeps one broken widget from blanking the whole app during a live session.
export default class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidUpdate(prev) { if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null }); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="boundary">
        <TriangleAlert size={20} />
        <b>This view hit an error</b>
        <small className="mono">{String(this.state.error?.message || this.state.error).slice(0, 200)}</small>
        <button className="ghost sm" onClick={() => this.setState({ error: null })}><RotateCcw size={13} /> Retry</button>
      </div>
    );
  }
}
