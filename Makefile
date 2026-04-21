REMOTE      := hetzner
REMOTE_APP  := /home/nicolas/maps_of_making
REMOTE_GW   := /home/nicolas/hetzner-gateway/nginx/conf.d

# Files/dirs excluded from app sync
RSYNC_EXCLUDE := \
	--exclude='.git/' \
	--exclude='_bmad/' \
	--exclude='_bmad-output/' \
	--exclude='archive/' \
	--exclude='*.mp4' \
	--exclude='*.zip' \
	--exclude='*.md' \
	--exclude='.claude/' \
	--exclude='gateway-nginx/'

.PHONY: sync sync-app sync-gateway help

help:
	@echo "make sync          — sync everything (app + gateway confs)"
	@echo "make sync-app      — sync web/, infra/, data/ to VPS"
	@echo "make sync-gateway  — sync gateway nginx confs (manual reload needed)"

## Push web/, infra/, data/ to VPS and sync gateway nginx confs
sync: sync-app sync-gateway

## Push app files only (web + infra + data skeleton)
sync-app:
	rsync -avz --delete $(RSYNC_EXCLUDE) \
		web infra data \
		$(REMOTE):$(REMOTE_APP)/
	@echo "✓ app synced to $(REMOTE):$(REMOTE_APP)"

## Push gateway nginx confs only (triggers manual nginx reload on VPS)
sync-gateway:
	rsync -avz \
		infra/gateway-nginx/ \
		$(REMOTE):$(REMOTE_GW)/
	@echo "✓ gateway confs synced to $(REMOTE):$(REMOTE_GW)"
	@echo "  → reload nginx manually if conf changed: ssh $(REMOTE) 'docker exec nginx-gateway nginx -s reload'"
