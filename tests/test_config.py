def test_configuracoes_obrigatorias():
    assert hasattr(config, 'LLM_GENERAL_BASE_URL')
    assert hasattr(config, 'LLM_CODER_BASE_URL')

def test_validacao_caminhos():
    assert validar_caminho_arquivo('teste.txt')
    assert not validar_caminho_arquivo('/etc/passwd')
