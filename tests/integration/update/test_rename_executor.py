import os

from jina import Client, Document, DocumentArray, Flow

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path, remove_prefix

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
rename_executor_flow_file = 'custom_name_executor.yml'
expsoed_executor_flow_file = 'expose_executor.yml'
rename_expsoed_executor_flow_file = 'custom_name_exposed_executor.yml'
protocol = 'http'


def test_rename_executor():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        flow.path = os.path.join(flows_dir, rename_executor_flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)

        assert (
            get_dict_list_key_path(status, ['spec', 'executors', 0, 'name'])
            == 'newsentencizer'
        )

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50


def test_rename_exposed_executor():
    with CloudFlow(path=os.path.join(flows_dir, expsoed_executor_flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        assert 'executor0' in flow.endpoints
        assert flow.endpoints['executor0'].startswith('grpcs://executor0')

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        flow.path = os.path.join(flows_dir, rename_expsoed_executor_flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        assert 'newsentencizer' in flow.endpoints
        assert flow.endpoints['newsentencizer'].startswith('grpcs://newsentencizer')
        exc_host = flow.endpoints['newsentencizer']

        status = flow._loop.run_until_complete(flow.status)

        assert (
            get_dict_list_key_path(status, ['spec', 'executors', 0, 'name'])
            == 'newsentencizer'
        )

        import time

        time.sleep(20)

        with Flow(protocol='HTTP').add(
            host=remove_prefix(exc_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50
