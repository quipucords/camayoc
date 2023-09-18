import random
import time
from uuid import uuid4

from camayoc.config import settings
from camayoc.qpc_models import Scan
from camayoc.qpc_models import ScanJob


def test_reproduce_426(data_provider):
    for source_definition in settings.sources:
        if source_definition.type == "vcenter":
            break

    credential_name = random.choice(source_definition.credentials)
    credential_model = data_provider.credentials.new_one({"name": credential_name}, data_only=True)
    credential_model.create()

    source_model = data_provider.sources.new_one(
        {"name": source_definition.name}, new_dependencies=True, data_only=True
    )
    source_model.credentials = [credential_model._id]
    source_model.create()

    scan_model = Scan(name=str(uuid4()), source_ids=[source_model._id])
    scan_model.create()

    data_provider.mark_for_cleanup(credential_model, source_model, scan_model)

    scj = ScanJob(scan_id=scan_model._id)
    scj.create()
    time.sleep(random.randint(1, 5))
    data_provider.cleanup()
