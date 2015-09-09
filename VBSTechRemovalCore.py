import sys
import re
import pyparsing as pp

# Entry class responsible for replacing all mentions of the technology for #0#/#1# 
class TechRemover:    
    def __init__(self, code, technology, alwaysTrue, log):
        self.code = code
        self.newCode = []
        self.tech = technology
        self.tech_re = '[ \t]*' + technology + '[ \t]*'
        self.delimiter_left = '(?P<ldelimiter>[ \t&\|\(])'
        self.delimiter_right = '(?P<rdelimiter>[ \t&\|\)])'
        self.log = log
        self.alwaysTrue = alwaysTrue
        self.anyChange = False
        self.simplifier = ExpressionSimplifier()
        self.rep = re.compile(r"^(?P<start>[ \t]*#[ \t]*(?:el)?if(?:n)?(?:def)?[ \t]+)(?P<inside>[^/\n]+)(?P<end>[ \t]*(?://.*)?(?:/\*.*\*/[ \t]*)?\n)$")
        
        #defined and not defined
        self.rgx_notdefined = re.compile('![ \t]*defined[ \t]' + self.tech_re + '[ \t]')
        self.rgx_notdefined_param = re.compile('![ \t]*defined[ \t]*\(' + self.tech_re + '\)')
        self.rgx_defined = re.compile('defined[ \t]' + self.tech_re + '[ \t]')
        self.rgx_defined_param = re.compile('defined[ \t]*\(' + self.tech_re + '\)')
        
        #normal
        self.rgx_not_normal = re.compile('!' + self.tech_re + self.delimiter_right)
        self.rgx_normal = re.compile(self.delimiter_left + self.tech_re + self.delimiter_right)
        self.rgx_normal_start = re.compile('^' + self.tech_re + self.delimiter_right)

        #brackets
        self.rgx_brackets = re.compile('\(' + self.tech_re + '\)')
        self.rgx_not_brackets = re.compile('!\(' + self.tech_re + '\)')
    
    def replaceTechInside(self,text):
        #add dummy space at the end to more easily deal with endings and simplify the regexes
        dummy = text+' '
        #defined and not defined
        dummy = self.rgx_notdefined.sub('#%d#'%(not self.alwaysTrue), dummy)
        dummy = self.rgx_notdefined_param.sub('#%d#'%(not self.alwaysTrue), dummy)
        dummy = self.rgx_defined.sub('#%d#'%(self.alwaysTrue), dummy)
        dummy = self.rgx_defined_param.sub('#%d#'%(self.alwaysTrue), dummy)
        #brackets
        #dummy = self.rgx_brackets.sub('#%d#'%(self.alwaysTrue), dummy)
        dummy = self.rgx_not_brackets.sub('#%d#'%(not self.alwaysTrue), dummy)
        #normal
        dummy = self.rgx_normal_start.sub('#%d#\\g<rdelimiter>'%(self.alwaysTrue), dummy)
        dummy = self.rgx_not_normal.sub('#%d#\\g<rdelimiter>'%(not self.alwaysTrue), dummy)
        dummy = self.rgx_normal.sub('\\g<ldelimiter>#%d#\\g<rdelimiter>'%(self.alwaysTrue), dummy)
        #remove the dummy space
        return dummy.rstrip()
    
    def replaceAllMentions(self,cline,lnumber,lrange=1):
        findifelif = self.rep.search(cline)
        if(findifelif!=None):
            start = findifelif.group('start')
            insides = findifelif.group('inside')
            end = '' if findifelif.group('end') is None else findifelif.group('end')
            if range == 1:
                if(not self.log is None): self.log.write('\tFound (el)if(def) on line %d replacing tech:%s\tinsides:%s\n' % (lnumber,cline,insides))
            else:
                if(not self.log is None): self.log.write('\tFound (el)if(def) on lines %d-%d replacing tech:%s\tinsides:%s\n' % (lnumber,lnumber+lrange,cline,insides))
            try:
                changed = self.replaceTechInside(insides)
            except pp.ParseException, e:
                print str(e)
                if(not self.log is None): self.log.write('\t\t Tech replacement failed:%s' % (start + insides + end))
            if(changed!=insides.rstrip()):
                self.anyChange = True
                if(not self.log is None): self.log.write('\t\t Tech replaced:%s' % (start + changed + end))
                try:
                    changed = self.simplifier.process(changed)
                    if(self.simplifier.anyChange and not self.log is None): self.log.write('\t Simplified to:%s' % (start + changed + end))
                except pp.ParseException, e:
                    print str(e)
                    if(not self.log is None): self.log.write('\t\t Simplification failed:%s' % (start + changed + end))
                self.simplifier.reset()
                if end.rstrip() != '':
                    changed += ' '
                self.newCode.append(start + changed + end)
                return
        for i in range(lrange-1,-1,-1):
            self.newCode.append(self.code[lnumber-i])
    
    def process(self):
        lines = ""
        lrange = 0
        for lnumber,cline in enumerate(self.code):
            if lrange > 0:
                lrange += 1
                if cline.rstrip().endswith('\\'):
                    #we still need to continue
                    lines += cline.rstrip()[:-1] + ' '
                else:
                    #finally we can start replacing
                    lines += cline
                    self.replaceAllMentions(lines,lnumber,lrange)
                    lrange = 0
            else:
                findifelif = self.rep.search(cline)
                if(findifelif!=None):
                    #(el)if started
                    if cline.rstrip().endswith('\\'):
                        #we need to continue
                        lines = cline.rstrip()[:-1] + ' '
                        lrange = 1
                    else:
                        self.replaceAllMentions(cline,lnumber)
                else:
                    self.replaceAllMentions(cline,lnumber)
        if(self.anyChange):
            self.code = self.newCode
            #clean
            while True:
                cleaner = RemovedTechCleaner(self.code,self.log)
                cleaner.process()
                if(cleaner.anyChange):
                    self.code = cleaner.newCode
                else:
                    break
                
#Class responsible for simplifying conditions and hopefully removing #0# and #1# in the process
class ExpressionSimplifier:
    def __init__(self):
        name = pp.Regex(r"(!?[_a-zA-z]\w*[ \t]*(?:[<>=]=?[ \t]*\d+)?)|(?:defined)|[01]")
        self.grammar = pp.Literal('#0#') | pp.Literal('#1#') | name | pp.Literal('&&') | pp.Literal('||') | pp.Literal("!")
        self.nestedgrammar = pp.nestedExpr('(', ')', self.grammar)
        self.anyChange = False
        self.iterChange = False
        self.addParentheses = False
        self.funResult = -1

    def sublistExists(self, list, sublist):
        for i in range(len(list)-len(sublist)+1):
            if sublist == list[i:i+len(sublist)]:
                return i
        return -1

    def predZeroAndSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#0#' in x) and ('&&' in x)
    def predZeroOrSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#0#' in x) and ('||' in x)
    def predOneOrSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#1#' in x) and ('||' in x)
    def predOneAndSmt(self,x):
        return len(x)>=3 and len(x)<=4 and ('#1#' in x) and ('&&' in x)
    def predZeroAllAnd(self,x):
        return len(x)>=3 and ('#0#' in x) and ('||' not in x)
    def predOneAllOr(self,x):
        return len(x)>=3 and ('#1#' in x) and ('&&' not in x)
    def predZeroAllOr(self,x):
        return len(x)>=3 and ('#0#' in x) and ('&&' not in x)
    def predOneAllAnd(self,x):
        return len(x)>=3 and ('#1#' in x) and ('||' not in x)
    def predSingleton(self,x):
        return len(x)==1 and type(x[0]) is list
    def funNotOne(self,x):
        self.funResult = self.sublistExists(x,['!','#1#'])
        return self.funResult
    def funNotZero(self,x):
        self.funResult = self.sublistExists(x,['!','#0#'])
        return self.funResult
    def funDefZero(self,x):
        self.funResult = self.sublistExists(x,['defined','#0#'])
        return self.funResult
    def funDefOne(self,x):
        self.funResult = self.sublistExists(x,['defined','#1#'])
        return self.funResult
    def funNDefZero(self,x):
        self.funResult = self.sublistExists(x,['!defined','#0#'])
        return self.funResult
    def funNDefOne(self,x):
        self.funResult = self.sublistExists(x,['!defined','#1#'])
        return self.funResult
    def funRightSingleton(self,x):
        pos = -1
        if pos == -1:
            pos = self.sublistExists(x,['&&',['#0#']])
        if pos == -1:
            pos = self.sublistExists(x,['&&',['#1#']])
        if pos == -1:
            pos = self.sublistExists(x,['||',['#0#']])
        if pos == -1:
            pos = self.sublistExists(x,['||',['#1#']])
        if pos == -1:
            pos = self.sublistExists(x,['!',['#0#']])
        if pos == -1:
            pos = self.sublistExists(x,['!',['#1#']])
        if pos == -1:
            pos = self.sublistExists(x,['defined',['#0#']])
        if pos == -1:
            pos = self.sublistExists(x,['defined',['#1#']])
        if pos == -1:
            pos = self.sublistExists(x,['!defined',['#0#']])
        if pos == -1:
            pos = self.sublistExists(x,['!defined',['#1#']])
        self.funResult = pos
        return self.funResult
    def funLeftSingleton(self,x):
        pos = -1
        if pos == -1:
            pos = self.sublistExists(x,[['#0#'],'&&'])
        if pos == -1:
            pos = self.sublistExists(x,[['#1#'],'&&'])
        if pos == -1:
            pos = self.sublistExists(x,[['#0#'],'||'])
        if pos == -1:
            pos = self.sublistExists(x,[['#1#'],'||'])
        self.funResult = pos
        return self.funResult
    def funSingleton(self,x):
        pos = -1
        if pos == -1:
            pos = self.sublistExists(x,[[['#0#']]])
        if pos == -1:
            pos = self.sublistExists(x,[[['#1#']]])
        self.funResult = pos
        return self.funResult

        
    def reset(self):
        self.anyChange = False
        self.iterChange = False
        
    def printResult(self,a,initP):
        if(isinstance(a,str)):
            if(a == '&&' or a == '||'):
                return ' '+a+' '
            elif(a == 'defined' or a == '!defined'):
                return a+' '
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

        if self.predSingleton(result):
            self.anyChange = True
            self.iterChange = True
            result = result[0]
        elif self.funSingleton(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result[pos] = result[pos][0]
        elif self.funLeftSingleton(result) == 0:
            self.anyChange = True
            self.iterChange = True
            result[0] = result[0][0]
        elif self.funRightSingleton(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result[pos+1] = result[pos+1][0]
        elif self.funNotOne(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#0#'
        elif self.funNotZero(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#1#'
        elif self.funDefOne(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#1#'
        elif self.funDefZero(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#0#'
        elif self.funNDefOne(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#0#'
        elif self.funNDefZero(result) != -1:
            self.anyChange = True
            self.iterChange = True
            pos = self.funResult
            result.pop(pos)
            result[pos] = '#1#'
        elif(self.predZeroAndSmt(result) or self.predZeroAllAnd(result)):
            self.anyChange = True
            self.iterChange = True
            result = '#0#'
        elif(self.predOneOrSmt(result) or self.predOneAllOr(result)):
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
        elif(self.predZeroAllOr(result)):
            self.anyChange = True
            self.iterChange = True
            pos = result.index("#0#")
            if pos-1 >= 0 and result[pos-1] == "||":
                result.pop(pos)
                result.pop(pos-1)
            elif pos+1 < len(result) and result[pos+1] == "||":
                result.pop(pos+1)
                result.pop(pos)
        elif(self.predOneAllAnd(result)):
            self.anyChange = True
            self.iterChange = True
            pos = result.index("#1#")
            if pos-1 >= 0 and result[pos-1] == "&&":
                result.pop(pos)
                result.pop(pos-1)
            elif pos+1 < len(result) and result[pos+1] == "&&":
                result.pop(pos+1)
                result.pop(pos)
        return result
        
    def process(self, insides):
        try:
          parsed = self.nestedgrammar.parseString("("+insides+")").asList()
        except:
          print "Unexpected error when parsing:\n", "("+insides+")", "\nusing:\n", self.nestedgrammar
          raise
        simpl = self.simplify(parsed)
        while(self.iterChange):
            self.iterChange = False
            simpl = self.simplify(simpl)
                
        return self.printResult(simpl[0] if self.predSingleton(simpl) else simpl,False)

       
class FSMDefaultState:
    def __init__(self):
        self.ifzero = re.compile(r"^[ \t]*#[ \t]*if(?:def)?[ \t]+#0#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)$")
        self.ifone = re.compile(r"^[ \t]*#[ \t]*if(?:def)?[ \t]+#1#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)$")
        self.ifndefzero = re.compile(r"^[ \t]*#[ \t]*ifndef[ \t]+#0#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)?$")
        self.ifndefone = re.compile(r"^[ \t]*#[ \t]*ifndef[ \t]+#1#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)?$")

        self.elifzero = re.compile(r"^[ \t]*#[ \t]*el(?:se)?if[ \t]+#0#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)$")
        self.elifone = re.compile(r"^[ \t]*#[ \t]*el(?:se)?if[ \t]+#1#[ \t]*(?P<end>(?://.*)?(?:/\*.*\*/[ \t]*)?\n)$")

        self.elseif = re.compile(r"^(?P<start>[ \t]*)#[ \t]*el(?P<seif>se|if[ \t])(?P<rest>[^\n]*\n)$")
        self.anyif = re.compile(r"^[ \t]*#[ \t]*if")
        self.endif = re.compile(r"^[ \t]*#[ \t]*endif")
        self.emptyLine = '#EMPTY#'    
    
    def processLine(self,cline):
        ifonesearch = self.ifone.search(cline)
        ifzerosearch = self.ifzero.search(cline)
        ifndefzerosearch = self.ifndefzero.search(cline)
        ifndefonesearch = self.ifndefone.search(cline)
        elifonesearch = self.elifone.search(cline)
        elifzerosearch = self.elifzero.search(cline)
        if(ifonesearch!=None):
            result = self.emptyLine if (ifonesearch.group('end') is None or ifonesearch.group('end') == '\n') else ifonesearch.group('end')
            return (result,'waitforelseifandremoveit')
        elif(ifzerosearch!=None):
            result = self.emptyLine #if (ifzerosearch.group('end') is None or ifzerosearch.group('end') == '\n') else ifzerosearch.group('end')
            return (result,'removeuntilelseif')
        elif(ifndefzerosearch!=None):
            result = self.emptyLine if (ifndefzerosearch.group('end') is None or ifndefzerosearch.group('end') == '\n') else ifndefzerosearch.group('end')
            return (result,'waitforelseifandremoveit')
        elif(ifndefonesearch!=None):
            result = self.emptyLine #if (ifndefonesearch.group('end') is None or ifndefonesearch.group('end') == '\n') else ifndefonesearch.group('end')
            return (result,'removeuntilelseif')
        elif(elifonesearch!=None):
            result = '#else\n' if (elifonesearch.group('end') is None or elifonesearch.group('end') == '\n') else '#else ' + elifonesearch.group('end')
            return (result,'waitelseifforelseifandremoveit')
        elif(elifzerosearch!=None):
            result = self.emptyLine #if (elifzerosearch.group('end') is None or elifzerosearch.group('end') == '\n') else elifzerosearch.group('end')
            return (result,'removeelseifuntilelseif')
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

class FSMWaitElseIfForElseIFAndRemoveIt(FSMDefaultState):
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
            return (cline,'default')

        if(not self.waitingForElseIf):
            return (self.emptyLine,self.getName())
        else:
            return (cline,self.getName())

    def getName(self):
        return 'waitelseifforelseifandremoveit'

class FSMRemoveElseIfUntilElseIf(FSMDefaultState):
    def __init__(self):
        FSMDefaultState.__init__(self)
        self.ifcounter = 0

    def resetMem(self):
        self.ifcounter = 0

    def processLine(self,cline):
        anyifsearch = self.anyif.search(cline)
        endifsearch = self.endif.search(cline)
        elseifsearch = self.elseif.search(cline)
        if(anyifsearch != None):
            self.ifcounter += 1
        if(endifsearch != None):
            self.ifcounter -= 1

        if(elseifsearch != None and self.ifcounter==0):
            self.resetMem()
            return (cline,'default')

        if(self.ifcounter == -1):
            self.resetMem()
            return (cline,'default')

        return (self.emptyLine,self.getName())

    def getName(self):
        return 'removeelseifuntilelseif'
 
#Class responsible for cleaning-up code of conditions with only #0# or #1# 
class RemovedTechCleaner:
    def __init__(self, code, log):
        self.code = code
        self.log = log
        self.anyChange = False
        self.newCode = []
        
        default = FSMDefaultState()
        waitandremove = FSMWaitForElseIFAndRemoveIt()
        removeuntil = FSMRemoveUntilElseIf()
        waitelseifandremove = FSMWaitElseIfForElseIFAndRemoveIt()
        removeelseifuntil = FSMRemoveElseIfUntilElseIf()
        self.states = {
            default.getName(): default,
            waitandremove.getName(): waitandremove,
            removeuntil.getName(): removeuntil,
            waitelseifandremove.getName(): waitelseifandremove,
            removeelseifuntil.getName(): removeelseifuntil
        }
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
