package auth

import (
	"os/exec"
	"strings"
)

// CodexStatus describes whether the local Codex CLI is installed and logged in.
type CodexStatus struct {
	Installed bool
	LoggedIn  bool
	Message   string
}

// CheckCodexStatus verifies that the local Codex CLI exists and is authenticated.
func CheckCodexStatus() CodexStatus {
	if _, err := exec.LookPath("codex"); err != nil {
		return CodexStatus{
			Installed: false,
			LoggedIn:  false,
			Message:   "Codex CLI is not installed. Install it, then run `codex login`.",
		}
	}

	out, err := exec.Command("codex", "login", "status").CombinedOutput()
	statusText := strings.TrimSpace(string(out))
	lower := strings.ToLower(statusText)

	if err != nil {
		return CodexStatus{
			Installed: true,
			LoggedIn:  false,
			Message:   "Codex CLI is not logged in. Run `codex login` and try again.",
		}
	}

	if strings.Contains(lower, "not logged in") || strings.Contains(lower, "logged out") {
		return CodexStatus{
			Installed: true,
			LoggedIn:  false,
			Message:   "Codex CLI is not logged in. Run `codex login` and try again.",
		}
	}

	if statusText == "" {
		statusText = "Codex CLI login is ready."
	}

	return CodexStatus{
		Installed: true,
		LoggedIn:  true,
		Message:   statusText,
	}
}
