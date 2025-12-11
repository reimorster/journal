# ================================
# Configuração padrão (pode sobrescrever na linha de comando)
# ================================

PREFIX    ?= $(HOME)
BINDIR    ?= $(PREFIX)/bin
NOTES_DIR ?= $(HOME)/notes

SCRIPTS   := ideia jnl sync_notes

# ================================
# Metas "públicas"
# ================================

.PHONY: all install uninstall init-notes install-scripts help

all: help

help:
	@echo "Targets"
	@echo "  make install        - Instala scripts em $(BINDIR) e prepara $(NOTES_DIR)"
	@echo "  make uninstall      - Remove scripts de $(BINDIR)"
	@echo "  make init-notes     - Cria $(NOTES_DIR) e inicializa repositório Git"
	@echo
	@echo "ENV Vars"
	@echo "  BINDIR=/caminho     - Diretório para instalar os scripts (padrão: $(BINDIR))"
	@echo "  NOTES_DIR=/caminho  - Diretório de notas/journal (padrão: $(NOTES_DIR))"

install: install-scripts init-notes
	@echo "✅ Installed"

uninstall:
	@echo "Removing scripts from $(BINDIR)..."
	@set -e; \
	for s in $(SCRIPTS); do \
		if [ -f "$(BINDIR)/$$s" ]; then \
			echo "  rm $(BINDIR)/$$s"; \
			rm -f "$(BINDIR)/$$s"; \
		else \
			echo "  (já não existe: $(BINDIR)/$$s)"; \
		fi; \
	done
	@echo "✅ Remoção concluída (notas em $(NOTES_DIR) não foram apagadas)."

# ================================
# Metas internas
# ================================

install-scripts:
	@echo "Instalando scripts em $(BINDIR)..."
	@mkdir -p "$(BINDIR)"
	@set -e; \
	for s in $(SCRIPTS); do \
		echo "  install -Dm755 scripts/$$s $(BINDIR)/$$s"; \
		install -Dm755 "scripts/$$s" "$(BINDIR)/$$s"; \
	done

init-notes:
	@echo "Preparando diretório de notas em $(NOTES_DIR)..."
	@mkdir -p "$(NOTES_DIR)/ideias" "$(NOTES_DIR)/journal"
	@cd "$(NOTES_DIR)" && \
	if [ ! -d ".git" ]; then \
		echo "  git init em $(NOTES_DIR)"; \
		git init >/dev/null; \
	else \
		echo "  Repositório Git já existe em $(NOTES_DIR)"; \
	fi
