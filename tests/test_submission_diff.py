import unittest
from agents.mis.submission_diff import compare_snapshots
from scripts.manage_demo import preflight
from unittest.mock import patch

class ReviewDiffTests(unittest.TestCase):
    def test_added_removed_and_changed_evidence(self):
        before={'dossier':{'references':[{'id':'a','title':'Old'}],'claims':[{'id':'c','statement':'Before'}]},'operations':{'generated_at':'yesterday'}}
        after={'dossier':{'references':[{'id':'b','title':'New'}],'claims':[{'id':'c','statement':'After'}]},'operations':{'generated_at':'today'}}
        changes=compare_snapshots(before,after)
        self.assertEqual([(c['field'],c['kind']) for c in changes],[('references','removed'),('references','added'),('claims','changed')])
        self.assertEqual(changes[-1]['before']['statement'],'Before')

    def test_no_docker_is_blocked_not_passed(self):
        with patch('scripts.manage_demo.shutil.which',return_value=None),patch('scripts.manage_demo.docker') as docker:
            result=preflight()
        self.assertFalse(result['ready'])
        self.assertEqual(result['checks'][-1]['status'],'blocked')
        docker.assert_not_called()
