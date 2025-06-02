"""
Script para monitorar o MCP Server.
"""

import os
import sys
from pathlib import Path
import argparse
import time
import json
import requests
from datetime import datetime
import psutil
import matplotlib.pyplot as plt
from typing import Dict, Any, List

# Adicionar diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

class MCPMonitor:
    """Monitor do MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Inicializa o monitor."""
        self.base_url = base_url
        self.metricas: Dict[str, List[Dict[str, Any]]] = {
            "cpu": [],
            "memoria": [],
            "disco": [],
            "tempo_resposta": [],
            "requisicoes": [],
            "erros": []
        }
        
    def coletar_metricas(self) -> Dict[str, Any]:
        """Coleta métricas do servidor."""
        try:
            response = requests.get(f"{self.base_url}/metricas")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao coletar métricas: {e}")
            return {}
            
    def coletar_relatorio(self) -> Dict[str, Any]:
        """Coleta relatório do servidor."""
        try:
            response = requests.get(f"{self.base_url}/relatorio")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao coletar relatório: {e}")
            return {}
            
    def monitorar(self, intervalo: int = 60, duracao: int = 3600):
        """Monitora o servidor por um período."""
        print(f"Iniciando monitoramento por {duracao} segundos")
        print(f"Intervalo de coleta: {intervalo} segundos")
        print("\nPressione Ctrl+C para parar")
        
        inicio = time.time()
        contador = 0
        
        try:
            while time.time() - inicio < duracao:
                # Coletar métricas
                metricas = self.coletar_metricas()
                if metricas:
                    timestamp = datetime.now().isoformat()
                    for nome, valor in metricas.items():
                        if nome in self.metricas:
                            self.metricas[nome].append({
                                "valor": valor,
                                "timestamp": timestamp
                            })
                            
                # Coletar relatório
                relatorio = self.coletar_relatorio()
                if relatorio:
                    print(f"\nRelatório {contador}:")
                    print(f"Agentes ativos: {relatorio['agentes']['ativos']}")
                    print(f"Ferramentas ativas: {relatorio['ferramentas']['total']}")
                    print(f"CPU: {metricas.get('cpu', 0)}%")
                    print(f"Memória: {metricas.get('memoria', 0)}%")
                    print(f"Disco: {metricas.get('disco', 0)}%")
                    
                contador += 1
                time.sleep(intervalo)
                
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuário")
            
        finally:
            self.salvar_metricas()
            self.gerar_graficos()
            
    def salvar_metricas(self, arquivo: str = "metricas_mcp.json"):
        """Salva as métricas coletadas."""
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(self.metricas, f, ensure_ascii=False, indent=2)
            print(f"\nMétricas salvas em {arquivo}")
        except Exception as e:
            print(f"Erro ao salvar métricas: {e}")
            
    def gerar_graficos(self):
        """Gera gráficos das métricas coletadas."""
        try:
            # Configurar estilo
            plt.style.use("seaborn")
            
            # Criar figura com subplots
            fig, axs = plt.subplots(3, 2, figsize=(15, 10))
            fig.suptitle("Métricas do MCP Server")
            
            # Plotar métricas
            metricas = ["cpu", "memoria", "disco", "tempo_resposta", "requisicoes", "erros"]
            titulos = {
                "cpu": "Uso de CPU (%)",
                "memoria": "Uso de Memória (%)",
                "disco": "Uso de Disco (%)",
                "tempo_resposta": "Tempo de Resposta (s)",
                "requisicoes": "Requisições",
                "erros": "Erros"
            }
            
            for i, metrica in enumerate(metricas):
                if metrica in self.metricas and self.metricas[metrica]:
                    ax = axs[i // 2, i % 2]
                    valores = [m["valor"] for m in self.metricas[metrica]]
                    timestamps = [m["timestamp"] for m in self.metricas[metrica]]
                    
                    ax.plot(timestamps, valores)
                    ax.set_title(titulos[metrica])
                    ax.set_xlabel("Tempo")
                    ax.set_ylabel("Valor")
                    ax.tick_params(axis="x", rotation=45)
                    
            plt.tight_layout()
            plt.savefig("metricas_mcp.png")
            print("Gráficos salvos em metricas_mcp.png")
            
        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Monitorar MCP Server")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="URL do MCP Server"
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=60,
        help="Intervalo de coleta em segundos"
    )
    parser.add_argument(
        "--duracao",
        type=int,
        default=3600,
        help="Duração do monitoramento em segundos"
    )
    
    args = parser.parse_args()
    
    monitor = MCPMonitor(args.url)
    monitor.monitorar(args.intervalo, args.duracao)
    
if __name__ == "__main__":
    main() 