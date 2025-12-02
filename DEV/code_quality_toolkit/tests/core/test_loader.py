"""Unit tests for the Plugin Loader (Task #177)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from toolkit.core.errors import PluginValidationError
from toolkit.core.loader import load_plugins

# --- Classes Auxiliares para Teste ---

class MockPlugin:
    """Uma classe de plugin válida para testes."""
    def get_metadata(self):
        return {
            "name": "TestPlugin",
            "version": "1.0",
            "description": "Test description"
        }
    
    def analyze(self, source, path):
        return {}

# --- Testes ---

@patch("toolkit.core.loader._iter_plugin_modules")
@patch("toolkit.core.loader._import_module_from_path")
def test_load_plugins_success(mock_import, mock_iter):
    """Testa o carregamento com sucesso de um plugin válido."""
    
    # 1. Arrange
    mock_iter.return_value = [("test_pkg", Path("/fake/path/plugin.py"))]
    
    # Simular o módulo importado
    mock_module = MagicMock()
    mock_module.Plugin = MockPlugin # Atribuir a classe real
    mock_import.return_value = mock_module
    
    # 2. Act
    plugins = load_plugins()

    # 3. Assert
    assert len(plugins) == 1
    assert "TestPlugin" in plugins
    # Verifica se é uma instância da nossa classe MockPlugin
    assert isinstance(plugins["TestPlugin"], MockPlugin)


@patch("toolkit.core.loader.logging.log")
@patch("toolkit.core.loader._iter_plugin_modules")
@patch("toolkit.core.loader._import_module_from_path")
def test_load_plugins_requested_filter(mock_import, mock_iter, mock_log):
    """
    Testa se o loader ignora plugins inexistentes e regista um aviso (plugin.missing)
    em vez de levantar uma exceção.
    """
    
    # 1. Arrange
    # Simula que existe um plugin chamado 'TestPlugin' (nome definido no MockPlugin)
    mock_iter.return_value = [("test_pkg", Path("/fake/path"))]
    
    mock_module = MagicMock()
    mock_module.Plugin = MockPlugin
    mock_import.return_value = mock_module
    
    # 2. Act
    # Pedimos um plugin que NÃO existe ("OutroPlugin")
    # O 'TestPlugin' (que existe) será ignorado porque não foi pedido.
    plugins = load_plugins(requested=["OutroPlugin"])
    
    # 3. Assert
    # O dicionário de plugins retornados deve estar vazio
    # (ou pelo menos não ter o OutroPlugin)
    assert "OutroPlugin" not in plugins
    
    # Verifica se o logger foi chamado com o evento e payload corretos
    mock_log.assert_called_with(
        "plugin.missing",
        level="ERROR",
        plugin="OutroPlugin",
        error="Requested plugins not found: OutroPlugin"
    )


@patch("toolkit.core.loader._iter_plugin_modules")
@patch("toolkit.core.loader._import_module_from_path")
def test_load_plugins_missing_class_attribute(mock_import, mock_iter):
    """Testa se o loader rejeita ficheiros sem a classe 'Plugin'."""
    
    mock_iter.return_value = [("bad_pkg", Path("/fake/path"))]
    
    # Módulo vazio (sem classe Plugin)
    bad_module = MagicMock()
    del bad_module.Plugin 
    # Garantir que o atributo não existe mesmo para o getattr
    bad_module = MagicMock(spec=[]) 
    
    mock_import.return_value = bad_module
    
    # Act & Assert
    with pytest.raises(PluginValidationError) as exc:
        load_plugins()
            
    assert "missing 'Plugin' attribute" in str(exc.value)