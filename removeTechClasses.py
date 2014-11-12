import re
import pyparsing as pp

class TechRemover:    
    def __init__(self, code, technology, alwaysTrue, log):
        self.code = code
        self.tech = technology
        self.log = log
        self.alwaysTrue = alwaysTrue
        self.anyChange = False
        self.simplifier = ExpressionSimplifier()
        self.rep = re.compile(r"^(?P<start>[ \t]*#[ \t]*(?:el)?if(?:n)?(?:def)?[ \t]+)(?P<inside>[^/\n]+)(?P<end>[ \t]*(?://.*)?\n)$")
    
    def replaceTechInside(self,text):    
        dummy = text+' '
        #defined and not defined
        dummy = re.sub('![ \t]*defined '+self.tech+' ?', ' #%d# '%(not self.alwaysTrue), dummy)
        dummy = re.sub('![ \t]defined ?\('+self.tech+'\)', ' #%d# '%(not self.alwaysTrue), dummy)
        dummy = re.sub('defined '+self.tech+' ?', ' #%d# '%(self.alwaysTrue), dummy)
        dummy = re.sub('defined ?\('+self.tech+'\)', ' #%d# '%(self.alwaysTrue), dummy)
        #normal
        dummy = re.sub('![ \t]*'+self.tech+' ', ' #%d# '%(not self.alwaysTrue), dummy)
        dummy = re.sub('[ \t]+'+self.tech+'[ \t]', ' #%d# '%(self.alwaysTrue), dummy)
        dummy = re.sub('[ \t]+'+self.tech+'\n', ' #%d# \n'%(self.alwaysTrue), dummy)
        return dummy[:-1]
    
    def replaceAllMentions(self,cline,lnumber):
        findifelif = self.rep.search(cline)
        if(findifelif!=None):
            start = findifelif.group('start')
            insides = findifelif.group('inside')
            end = '' if findifelif.group('end') is None else findifelif.group('end')
            if(not self.log is None): self.log.write('Found (el)if(def) on line %d replacing tech:%s' % (lnumber,cline))        
            changed = self.replaceTechInside(insides)
            if(changed!=insides):
                self.anyChange = True
                if(not self.log is None): self.log.write('\t Tech replaced:%s' % start + changed + end)
                changed = self.simplifier.process(changed)
                if(self.simplifier.anyChange and not self.log is None): self.log.write('\t Simplifed to:%s' % start + changed + end)
                self.simplifier.reset()
                self.code[lnumber] = start + changed + end
    
    def process(self):
        for lnumber,cline in enumerate(self.code):
            self.replaceAllMentions(cline,lnumber)
        if(self.anyChange):
            cleaner = RemovedTechCleaner(self.code,self.log)
            cleaner.process()
            if(cleaner.anyChange):
                self.code = cleaner.newCode

class ExpressionSimplifier:

    def __init__(self):
        name = pp.Regex(r"(!?[_a-zA-z]\w*[ \t]*(?:[<>]=?[ \t]*\d+)?)|(?:defined)|[01]")
        self.grammar = pp.Literal('#0#') | pp.Literal('#1#') | name | pp.Literal('&&') | pp.Literal('||') | pp.Literal("!")
        self.nestedgrammar  = pp.nestedExpr( '(', ')', self.grammar)
        self.anyChange = False
        self.iterChange = False
        
    def predZeroAndSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#0#' in x) and ('&&' in x)
    def predZeroOrSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#0#' in x) and ('||' in x)
    def predOneOrSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#1#' in x) and ('||' in x)
    def predOneAndSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#1#' in x) and ('&&' in x)
        
    def reset(self):
        self.anyChange = False
        self.iterChange = False
        
    def printResult(self,a,initP):
        if(isinstance(a,str)):
            if(a == '&&' or a == '||'):
                return ' '+a+' '
            else:
                return a
        else:
            result=''
            for x in a:
                result += self.printResult(x,True)
            if(initP):            
                return '('+result +')'
            else:
                return result
    
    def simplify(self,l):
        if(isinstance(l,str)):
            return l
        result = []
        for x in l:
            result.append(self.simplify(x))
            
        if(self.predZeroAndSmt(result)):
            self.anyChange = True
            self.iterChange = True
            result = '#0#'
        elif(self.predOneOrSmt(result)):
            self.anyChange = True
            self.iterChange = True
            result = '#1#'
        elif(self.predOneAndSmt(result)):
            self.anyChange = True
            self.iterChange = True
            result.remove("#1#")
            result.remove("&&")
        elif(self.predZeroOrSmt(result)):
            self.anyChange = True
            self.iterChange = True
            result.remove("#0#")
            result.remove("||")
        return result
        
    def process(self,insides):
        parsed = self.nestedgrammar.parseString("("+insides+")").asList()
        simpl = self.simplify(parsed)
        while(self.iterChange):
            self.iterChange = False
            simpl = self.simplify(simpl)
                
        return self.printResult(simpl[0],False)

        
class FSMDefaultState:
    def __init__(self):
        self.ifzero = re.compile(r"^[ \t]*#[ \t]*if(?:def)? +#0#[ \t]*(?P<end>(?://.*)?\n)$")
        self.ifone = re.compile(r"^[ \t]*#[ \t]*if(?:def)? +#1#[ \t]*(?P<end>(?://.*)?\n)$")
        self.ifndefzero = re.compile(r"^[ \t]*#[ \t]*ifndef +#0#[ \t]*(?P<end>(?://.*)?\n)?$")
        self.ifndefone = re.compile(r"^[ \t]*#[ \t]*ifndef +#1#[ \t]*(?P<end>(?://.*)?\n)?$")

        self.elseif = re.compile(r"^(?P<start>[ \t]*)#[ \t]*el(?P<seif>se|if )(?P<rest>[^\n]*\n)$")
        self.anyif = re.compile(r"^[ \t]*#[ \t]*if")
        self.endif = re.compile(r"^[ \t]*#[ \t]*endif")
        self.emptyLine = '#EMPTY#'    
    
    def processLine(self,cline):
        ifonesearch = self.ifone.search(cline)
        ifzerosearch = self.ifzero.search(cline)
        ifndefzerosearch = self.ifndefzero.search(cline)
        ifndefonesearch = self.ifndefone.search(cline)
        if(ifonesearch!=None):
            result = self.emptyLine if (ifonesearch.group('end') is None or ifonesearch.group('end') == '\n')  else ifonesearch.group('end')
            return (result,'waitforelseifandremoveit')
        elif(ifzerosearch!=None):
            result = self.emptyLine if (ifzerosearch.group('end') is None or ifzerosearch.group('end') == '\n') else ifzerosearch.group('end')
            return (result,'removeuntilelseif')
        elif(ifndefzerosearch!=None):
            result = self.emptyLine if (ifndefzerosearch.group('end') is None or ifndefzerosearch.group('end') == '\n') else ifndefzerosearch.group('end')
            return (result,'waitforelseifandremoveit')
        elif(ifndefonesearch!=None):
            result = self.emptyLine if (ifndefonesearch.group('end') is None or ifndefonesearch.group('end') == '\n') else ifndefonesearch.group('end')
            return (result,'removeuntilelseif')
        else:
            return (cline, self.getName())
            
    def getName(self):
        return 'default'

class FSMWaitForElseIFAndRemoveIt(FSMDefaultState):    
    def __init__(self):
        FSMDefaultState.__init__(self)
        self.ifcounter = 0
        self.waitingForElseIf = True
        
    def resetMem(self):
        self.ifcounter = 0
        self.waitingForElseIf = True

    def processLine(self,cline):
        anyifsearch = self.anyif.search(cline)
        endifsearch = self.endif.search(cline)
        elseifsearch = self.elseif.search(cline)
        if(anyifsearch != None):
            self.ifcounter += 1
        if(endifsearch != None):
            self.ifcounter -= 1
            
        if(elseifsearch != None and self.ifcounter==0):
            self.waitingForElseIf = False
            
        if(self.ifcounter == -1):
            self.resetMem()
            return (self.emptyLine,'default')        
     
        if(not self.waitingForElseIf):
            return (self.emptyLine,self.getName())
        else:
            return (cline,self.getName())
        
    def getName(self):
        return 'waitforelseifandremoveit'

class FSMRemoveUntilElseIf(FSMDefaultState):
    def __init__(self):
        FSMDefaultState.__init__(self)
        self.ifcounter = 0
        self.waitingForElseIf = True
        self.wasThereElif = False
        
    def resetMem(self):
        self.ifcounter = 0
        self.waitingForElseIf = True
        self.wasThereElif = False

    def processLine(self,cline):
        anyifsearch = self.anyif.search(cline)
        endifsearch = self.endif.search(cline)
        elseifsearch = self.elseif.search(cline)
        if(anyifsearch != None):
            self.ifcounter += 1
        if(endifsearch != None):
            self.ifcounter -= 1
            
        if(elseifsearch != None and self.ifcounter==0 and self.waitingForElseIf):
            self.waitingForElseIf = False
            if(elseifsearch.group('seif')=='if '):
                start = '' if elseifsearch.group('start') is None else elseifsearch.group('start')
                rest = '' if elseifsearch.group('rest') is None else elseifsearch.group('rest')
                self.wasThereElif = True
                return (start+'#if '+rest,self.getName())
            else:
                self.wasThereElif = False
                return (self.emptyLine,self.getName())
        
        if(self.ifcounter == -1):
            if(self.wasThereElif):
                self.resetMem()
                return (cline,'default')
            else:
                self.resetMem()
                return (self.emptyLine,'default')
            
        if(self.waitingForElseIf):
            return (self.emptyLine,self.getName())
        else:
            return (cline,self.getName())
        
    def getName(self):
        return 'removeuntilelseif'
        
class RemovedTechCleaner:
    def __init__(self, code, log):
        self.code = code
        self.log = log
        self.anyChange = False
        self.newCode = []
        
        default = FSMDefaultState()
        waitandremove = FSMWaitForElseIFAndRemoveIt()
        removeuntil = FSMRemoveUntilElseIf()
        self.states = {default.getName():default,waitandremove.getName():waitandremove,removeuntil.getName():removeuntil}
        self.currentState = self.states['default']
        
    def process(self):        
        for lnumber,cline in enumerate(self.code):
            processed = self.currentState.processLine(cline)
            if(not self.log is None): self.log.write('FSMS %s processed line %d\n' % (self.currentState.getName(),lnumber))
            self.currentState = self.states[processed[1]]
            if(processed[0]==self.states['default'].emptyLine):
                if(not self.log is None): self.log.write('\t and it removed it.\n')
                self.anyChange = True
            elif(processed[0]!=cline):
                if(not self.log is None): self.log.write('\t and change it to: %s\n' % (processed[0]))
                self.anyChange = True
                self.newCode.append(processed[0])
            else:
                self.newCode.append(cline)            
            
                
        
        
        