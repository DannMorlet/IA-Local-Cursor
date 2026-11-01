"""Servidor embebido de Manguito Studio, lanzado por el shell WebView2.

No genera ni imprime tokens: el shell padre lo configura en el entorno
del proceso. Nunca abre puertos fuera de localhost.
"""
from manguito.gateway import main

if __name__ == "__main__":
    main()
