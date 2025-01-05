import unittest

from recorder.validator import Validator
from datahandling.RecordedSession import RecordedSession
from recorder.Persistence import ItemPrompt, ComponentName

def unittests():
    return unittest.makeSuite(SessionTests)
  
  
class SessionTests(unittest.TestCase):
    
    def test_view_sessions(self):
        
        val = Validator()
        sessions = val.get_ideal_view("Spkr2_2_Session1")
        
        for comp in sessions['1'].components:
            print comp
        
        # The ideal state should have 4 sessions
        self.assertEqual(1, len(sessions), "Ideal state should have 1 sessions")

        # Session 2 should contain 6 components
        self.assertEqual(6, len(sessions[1].components))
        
        # Session 1 Component 11 should have 16 items
        self.assertEqual(16, len(sessions[0].components[0].items))
        
        
        
    def test_real_manifest_unwrap(self):
        
        val = Validator()
        results = val.get_manifest_view("../../test/sample_data/realdata", "Spkr1_1121_Session1")
        
        self.assertTrue(results.has_key('1'))
        session = results['1']
        
        self.assertEqual('1', session.id)
        self.assertEqual(1, len(session.components))
        
        component = session.components[0]
        self.assertEqual('12', component.id)
        self.assertEqual(3, len(component.items))
        
    
    def test_another_manifest_unwrap(self):
        
        val = Validator()
        results = val.get_manifest_view("../../test/sample_data/correct", "Spkr2_2_Session1")
        
        #print results
        
        self.assertTrue(results.has_key('1'))
        session = results['1']
        
        self.assertEqual('1', session.id)
        self.assertEqual(2, len(session.components))
        
        component = session.components[1]
        self.assertEqual('4', component.id)
        self.assertEqual(1, len(component.items))
        
    
    @unittest.skip("upload needs server configured") 
    def test_real_unwrap(self):
        
        val = Validator()
        
        print val.get_ideal_view("Spkr2_2_Session1")
        print val.get_manifest_view("../../test/sample_data/correct", "Spkr2_2_Session1")
        print val.get_actual_view("../../test/sample_data/correct", "Spkr2_2_Session1")
        
        
        
    def test_item_prompt(self):
        """Can we generate an item prompt given the component and item ids"""
        
        self.assertEqual(ItemPrompt(2,1), "bassinette")
        self.assertEqual(ItemPrompt(2,10), "drawing")
        self.assertEqual(ItemPrompt(16, 10), "Who says itches are always so tempting to scratch?")
        