from syncmaster.scheduler.celery import app as celery

celery.conf.update(imports=list(celery.conf.imports) + ["tests.test_integration.test_scheduler.test_task"])
