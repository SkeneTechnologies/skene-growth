package config

import (
	"os"
	"strings"
	"testing"
)

func TestGetProvidersIncludesCodex(t *testing.T) {
	provider := GetProviderByID("codex")
	if provider == nil {
		t.Fatalf("expected codex provider to be registered")
	}
	if provider.RequiresKey {
		t.Fatalf("expected codex provider to avoid stored API keys")
	}
	if len(provider.Models) == 0 || provider.Models[0].ID != "auto" {
		t.Fatalf("expected codex provider to default to auto model")
	}
}

func TestHasValidConfigAllowsCodexWithoutAPIKey(t *testing.T) {
	mgr := NewManager(t.TempDir())
	mgr.Config.Provider = "codex"
	mgr.Config.Model = "auto"
	mgr.Config.APIKey = ""

	if !mgr.HasValidConfig() {
		t.Fatalf("expected codex config without api key to be valid")
	}
}

func TestSaveUserConfigRemovesClearedLLMCredentials(t *testing.T) {
	tempDir := t.TempDir()
	mgr := NewManager(tempDir)
	mgr.UserConfigPath = tempDir + "/config"

	initial := strings.Join([]string{
		`api_key = "old-key"`,
		`provider = "openai"`,
		`model = "gpt-5.4"`,
		`base_url = "https://example.com/v1"`,
		`output_dir = "./skene-context"`,
		"",
	}, "\n")
	if err := os.WriteFile(mgr.UserConfigPath, []byte(initial), 0600); err != nil {
		t.Fatalf("write initial config: %v", err)
	}

	mgr.Config.Provider = "codex"
	mgr.Config.Model = "auto"
	mgr.Config.OutputDir = "./skene-context"
	mgr.ClearLLMCredentials()

	if err := mgr.SaveUserConfig(); err != nil {
		t.Fatalf("save user config: %v", err)
	}

	data, err := os.ReadFile(mgr.UserConfigPath)
	if err != nil {
		t.Fatalf("read saved config: %v", err)
	}
	content := string(data)
	if strings.Contains(content, "api_key") {
		t.Fatalf("expected api_key to be removed, got:\n%s", content)
	}
	if strings.Contains(content, "base_url") {
		t.Fatalf("expected base_url to be removed, got:\n%s", content)
	}
	if !strings.Contains(content, `provider = "codex"`) {
		t.Fatalf("expected provider to remain, got:\n%s", content)
	}
	if !strings.Contains(content, `model = "auto"`) {
		t.Fatalf("expected model to remain, got:\n%s", content)
	}

	reloaded, err := mgr.loadConfigFile(mgr.UserConfigPath)
	if err != nil {
		t.Fatalf("reload config: %v", err)
	}
	if reloaded.APIKey != "" {
		t.Fatalf("expected API key to stay cleared, got %q", reloaded.APIKey)
	}
	if reloaded.BaseURL != "" {
		t.Fatalf("expected base URL to stay cleared, got %q", reloaded.BaseURL)
	}
}
