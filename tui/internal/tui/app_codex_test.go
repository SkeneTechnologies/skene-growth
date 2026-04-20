package tui

import (
	"path/filepath"
	"testing"

	"skene/internal/services/auth"
	"skene/internal/services/config"
)

func newTestApp(t *testing.T) *App {
	t.Helper()

	app := NewApp()
	app.width = 120
	app.height = 40
	tmpDir := t.TempDir()
	app.configMgr.ProjectConfigPath = filepath.Join(tmpDir, ".skene.config")
	app.configMgr.UserConfigPath = filepath.Join(tmpDir, "config")
	return app
}

func TestCodexAuthFlowStaysOnAuthViewWhenLoggedOut(t *testing.T) {
	app := newTestApp(t)
	provider := config.GetProviderByID("codex")
	if provider == nil {
		t.Fatalf("expected codex provider")
	}
	app.selectedProvider = provider
	app.selectedModel = &provider.Models[0]
	app.configMgr.SetProvider(provider.ID)
	app.configMgr.SetModel(app.selectedModel.ID)

	original := checkCodexStatus
	checkCodexStatus = func() auth.CodexStatus {
		return auth.CodexStatus{
			Installed: true,
			LoggedIn:  false,
			Message:   "Codex CLI is not logged in. Run `codex login` and try again.",
		}
	}
	defer func() { checkCodexStatus = original }()

	cmd := app.startCodexAuthCheck(StateModelSelect)
	msg := cmd()
	updatedModel, _ := app.Update(msg)
	updated := updatedModel.(*App)

	if updated.state != StateCodexAuth {
		t.Fatalf("expected state %v, got %v", StateCodexAuth, updated.state)
	}
	if updated.codexAuthView == nil {
		t.Fatalf("expected codex auth view to be active")
	}
	if updated.projectDirView != nil {
		t.Fatalf("did not expect project dir view while logged out")
	}
}

func TestCodexAuthFlowTransitionsToProjectDirWhenLoggedIn(t *testing.T) {
	app := newTestApp(t)
	provider := config.GetProviderByID("codex")
	if provider == nil {
		t.Fatalf("expected codex provider")
	}
	app.selectedProvider = provider
	app.selectedModel = &provider.Models[0]
	app.configMgr.SetProvider(provider.ID)
	app.configMgr.SetModel(app.selectedModel.ID)

	original := checkCodexStatus
	checkCodexStatus = func() auth.CodexStatus {
		return auth.CodexStatus{
			Installed: true,
			LoggedIn:  true,
			Message:   "Logged in using ChatGPT",
		}
	}
	defer func() { checkCodexStatus = original }()

	cmd := app.startCodexAuthCheck(StateModelSelect)
	msg := cmd()
	updatedModel, _ := app.Update(msg)
	updated := updatedModel.(*App)

	if updated.state != StateProjectDir {
		t.Fatalf("expected state %v, got %v", StateProjectDir, updated.state)
	}
	if updated.projectDirView == nil {
		t.Fatalf("expected project dir view to be active")
	}
}

func TestCodexAuthEscReturnsToConfigCheckWhenStartedFromExistingConfig(t *testing.T) {
	app := newTestApp(t)
	provider := config.GetProviderByID("codex")
	if provider == nil {
		t.Fatalf("expected codex provider")
	}
	app.selectedProvider = provider
	app.selectedModel = &provider.Models[0]
	app.configMgr.SetProvider(provider.ID)
	app.configMgr.SetModel(app.selectedModel.ID)

	original := checkCodexStatus
	checkCodexStatus = func() auth.CodexStatus {
		return auth.CodexStatus{
			Installed: true,
			LoggedIn:  false,
			Message:   "Codex CLI is not logged in. Run `codex login` and try again.",
		}
	}
	defer func() { checkCodexStatus = original }()

	cmd := app.startCodexAuthCheck(StateConfigCheck)
	msg := cmd()
	updatedModel, _ := app.Update(msg)
	updated := updatedModel.(*App)

	updated.handleCodexAuthKeys("esc")

	if updated.state != StateConfigCheck {
		t.Fatalf("expected state %v, got %v", StateConfigCheck, updated.state)
	}
}

func TestCodexAuthEscReturnsToModelSelectWhenStartedFromModelSelect(t *testing.T) {
	app := newTestApp(t)
	provider := config.GetProviderByID("codex")
	if provider == nil {
		t.Fatalf("expected codex provider")
	}
	app.selectedProvider = provider
	app.selectedModel = &provider.Models[0]
	app.configMgr.SetProvider(provider.ID)
	app.configMgr.SetModel(app.selectedModel.ID)

	original := checkCodexStatus
	checkCodexStatus = func() auth.CodexStatus {
		return auth.CodexStatus{
			Installed: true,
			LoggedIn:  false,
			Message:   "Codex CLI is not logged in. Run `codex login` and try again.",
		}
	}
	defer func() { checkCodexStatus = original }()

	cmd := app.startCodexAuthCheck(StateModelSelect)
	msg := cmd()
	updatedModel, _ := app.Update(msg)
	updated := updatedModel.(*App)

	updated.handleCodexAuthKeys("esc")

	if updated.state != StateModelSelect {
		t.Fatalf("expected state %v, got %v", StateModelSelect, updated.state)
	}
}
