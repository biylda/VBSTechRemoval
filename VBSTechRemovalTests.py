import unittest
import VBSTechRemovalCore
import re
import string
import StringIO

def cleanWhitespaces(text):
    cleaned = re.sub(r'\t+',r' ',text)
    cleaned = re.sub(r' +',r' ',cleaned)
    return cleaned

# C codes upon which the tests are run are in text files in \testfiles
# 'of' is a file with tested code
# 'ef' is a file with expected result of VBSTechRemoval script
class BareMinimumTest(unittest.TestCase):
    def common_test_procedure(self,origfile,expectedfile,tech,alwaysTrue):
        of = open(origfile, 'rU')
        ef = open(expectedfile, 'rU')    
        
        #logOutput = StringIO.StringIO()
        logOutput = open('VBSTechRemovalTests.log','a')
        
        oflines = of.readlines()
        eflines = ef.readlines()
        
        remover = VBSTechRemovalCore.TechRemover(oflines, tech, alwaysTrue, logOutput)
        remover.process()        
       
        logOutput.close()
        
        self.assertEqual(cleanWhitespaces(''.join(eflines)),cleanWhitespaces(''.join(remover.code)))
        
    def test_simple_if_true(self):
        self.common_test_procedure('testfiles/simple_if_orig.txt','testfiles/simple_if_true_exp.txt','_SOME_TECH',True)
    def test_simple_if_false(self):
        self.common_test_procedure('testfiles/simple_if_orig.txt','testfiles/simple_if_false_exp.txt','_SOME_TECH',False)
    def test_simple_ifdefdefine_true(self):
        self.common_test_procedure('testfiles/simple_ifdefdefined_orig.txt','testfiles/simple_ifdefdefined_true_exp.txt','_SOME_TECH',True)
    def test_simple_ifdefdefine_false(self):
        self.common_test_procedure('testfiles/simple_ifdefdefined_orig.txt','testfiles/simple_ifdefdefined_false_exp.txt','_SOME_TECH',False)
    def test_simple_not_true(self):
        self.common_test_procedure('testfiles/simple_not_orig.txt','testfiles/simple_not_true_exp.txt','_SOME_TECH',True)
    def test_simple_not_false(self):
        self.common_test_procedure('testfiles/simple_not_orig.txt','testfiles/simple_not_false_exp.txt','_SOME_TECH',False)
    def test_simple_else_true(self):
        self.common_test_procedure('testfiles/simple_else_orig.txt','testfiles/simple_else_true_exp.txt','_SOME_TECH',True)
    def test_simple_else_false(self):
        self.common_test_procedure('testfiles/simple_else_orig.txt','testfiles/simple_else_false_exp.txt','_SOME_TECH',False)
    def test_simple_elif_true(self):
        self.common_test_procedure('testfiles/simple_elif_orig.txt','testfiles/simple_elif_true_exp.txt','_SOME_TECH',True)
    def test_simple_elif_false(self):
        self.common_test_procedure('testfiles/simple_elif_orig.txt','testfiles/simple_elif_false_exp.txt','_SOME_TECH',False)
    def test_unexpected_whitespaces(self): 
        self.common_test_procedure('testfiles/simple_whitespaces_orig.txt','testfiles/simple_whitespaces_exp.txt','_SOME_TECH',True)
if __name__ == '__main__':
    unittest.main()
        
    