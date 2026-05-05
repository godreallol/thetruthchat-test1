import random, copy
from tabnanny import check

from quart import request, redirect, url_for, jsonify
from spacy.tokens import Doc


def register_ask_route(app, dependencies):
    nlp = dependencies["nlp"]
    get_current_user = dependencies["get_current_user"]
    get_session_chats = dependencies["get_session_chats"]
    find_chat = dependencies["find_chat"]
    build_user_state = dependencies["build_user_state"]
    save_session_chats = dependencies["save_session_chats"]
    build_state = dependencies["build_state"]
    append_db_message = dependencies["append_db_message"]
    wants_json = dependencies["wants_json"]
    build_chat_title = dependencies["build_chat_title"]

    @app.route("/ask", methods=["POST"])
    async def ask():
        form = await request.form
        question = form.get("question", "")
        chat_id = form.get("chat_id", "")
        current_user = get_current_user()

        if current_user is None:
            chats = get_session_chats()
            active_chat = find_chat(chats, chat_id) if chat_id else None
            if active_chat is None:
                active_chat = chats[0]
                chat_id = active_chat["id"]
        else:
            state = build_user_state(current_user["id"], chat_id)
            chats = state["chats"]
            active_chat = find_chat(chats, state["active_chat_id"])
            chat_id = state["active_chat_id"]

        
        Ndefinitions = {"a lot": "ab", "ab": "a lot", "ac": "ad", "ad": "ac", "ae": "a lot", "af": "ac", "ag": "ab", "ah": "ag"}
        Vdefinitions = {"running": ["walking",None], "walking": ["running", None], "cooking": ["walking",'ah'],"exhaling": ["cooking",None], "eating": ["sleeping",None], "sleeping": ["dying",None]}

        def build_question_help_answer():
            known_words = sorted(
                set(Ndefinitions.keys())
                | set(Ndefinitions.values())
                | set(Vdefinitions.keys())
                | {definition[0] for definition in Vdefinitions.values()}
                | {definition[1] for definition in Vdefinitions.values() if definition[1] is not None}
            )
            return [
                [['Ask', 'an', '"is X Y"', 'Question'], ['v', 'd', 'adj', 'n']],
                
                [['Known', 'Words', ':-', '"' + ", ".join(known_words) + '"'],
                ['adj', 'n', 'pu','n']],

                [['Example', ':-'],
                ['n', 'pu']],

                [['•', 'is', 'running', 'a lot', 'cooking'],
                ['pu', 'v', ['g', '+1'], 'g', 'g']],

                [['•', 'is', 'cooking', 'ah'],
                ['pu', 'v', 'g', 'n']],

                [['•', 'is', 'eating', 'sleeping'],
                ['pu', 'v', 'g', 'g']],
            ]

        answer = []
        question = question.strip()
        if not question:
            answer = build_question_help_answer()
            if current_user is None:
                active_chat["history"].append(["", answer])
                save_session_chats(chats, chat_id)
                state = build_state(chats, active_chat)
            else:
                append_db_message(current_user["id"], chat_id, "", answer)
                state = build_user_state(current_user["id"], chat_id)
            if await wants_json():
                return jsonify(state)
            return redirect(url_for("home", chat=state["active_chat_id"]))

        quelist = question.lower().split()

        try:
            doc = Doc(nlp.vocab, words=quelist)
            doc = nlp(doc)
        except Exception:
            doc = None

        def checkcompounds(splitstart, splitend):
            CAWords = []
            CBWords = []
            fullcompound = False
            currentword = ""
            VBStartIndex = None

            for i, v in enumerate(quelist):
                if i < splitstart:
                    continue
                elif i > splitend:
                    break
    
                if i == splitstart:
                    currentword = v
                else:
                    currentword += " "+v
            
                if i != splitend and currentword in Ndefinitions:
                    CAWords.append(i)
                elif i == splitend and currentword in Ndefinitions:
                    fullcompound = True

                
            currentword = ""
        
            for i, v in enumerate(reversed(quelist)):
                if i < len(quelist)-(1+splitend):
                    continue
                elif i == len(quelist)-(1+splitstart):
                    break
            
                if i == len(quelist)-(1+splitend):
                    currentword = v
                else:
                    currentword = v + " "+currentword

                if currentword in Ndefinitions:
                    CBWords.append(len(quelist)-i-1)

            midpoint = None

            if (len(quelist)-1) % 2 == 0:
                midpoint = (len(quelist)-1)/2 + 1
            else:
                midpoint = (len(quelist)-1)/2 + 0.5
    

            if len(CAWords) == 0 and len(CBWords) == 0:
                VBStartIndex = midpoint     
            elif len(CAWords) == 0 and len(CBWords) > 0:
                VBStartIndex = min(CBWords)
            elif len(CAWords) > 0 and len(CBWords) == 0:
                VBStartIndex = max(CAWords)
            else:
                consindexes = []
                for v in CAWords:
                    if v + 1 in CBWords:
                        consindexes.append(v + 1)

                if len(consindexes) == 0:
                    AHighest = max(CAWords)
                    BHighest = len(quelist) - min(CBWords)
                    if AHighest > BHighest or AHighest == BHighest:
                        VBStartIndex = AHighest
                    elif BHighest > AHighest:
                        VBStartIndex = BHighest
                else:
                    closest = min(consindexes, key=lambda x: abs(x - midpoint))
                    VBStartIndex = closest
                
            return VBStartIndex, CAWords, CBWords, fullcompound
    
        def prooftextcreator(obj1, obj2, waytoproof, therefore = False, knownproof = False):
        


            assumptionstext = []
            reasoningtext = []

            proofcompleted = False
            nextconnector = obj2
            proofoftext = [[["Assuming","with","data",":-"],['v','prp','n','pu']]]
            
            for reverseI, proofStepList in enumerate(reversed(waytoproof)):
            
            
                for proofStep in proofStepList:
                

                    if nextconnector in (proofStep[0], proofStep[1]):

                        
                    

                        oldnextconnector = nextconnector




                        if nextconnector == proofStep[0]:
                            nextconnector = proofStep[1]
                        elif nextconnector == proofStep[1]:
                            nextconnector = proofStep[0]

                        if reverseI + 1 != len(waytoproof) and knownproof == False:
                            i = len(waytoproof) - 1 - reverseI
                            nextproofStepList = waytoproof[i-1]
                            nextconnectorIsTrue = False
                            for nextproofStep in nextproofStepList:
                                if nextconnector in (nextproofStep[0], nextproofStep[1]):
                                    nextconnectorIsTrue = True
                                    break
                            if nextconnectorIsTrue == False:
                                nextconnector = oldnextconnector
                                break

                        if len(proofStep) == 3:
                            assumptionstext = proofStep[2]+assumptionstext

                            if nextconnector == obj1:
                                proofcompleted = True
                                break
                            continue


                        
                            

                        code = [None,None]
                        equalTexts = [None, None]
                        for i, step in enumerate(proofStep):
                            if step[1] == None:
                                code[i] = ['n']
                                equalTexts[i] = [step[0]]
                            elif step[1][0][1] == None:
                                code[i] = ['g']
                                equalTexts[i] = [step[1][0][0]]
                            else:
                                code[i] = [['g','+1'],'n']
                                equalTexts[i] = [step[1][0][0] , step[1][0][1]]
                        equalTexts[0][0] = equalTexts[0][0].capitalize()
                    
                        assumptionstext.insert(0, [equalTexts[0]+["is"]+equalTexts[1],code[0]+["v"]+code[1]])

                        #reasoningtext.insert(0, [["Since"]+equalTexts[0]+["is"]+equalTexts[1]+[","], ['prp']+code[0]+['v']+code[1]])
                        




                        if nextconnector == obj1:
                            proofcompleted = True
                        break
        
                if proofcompleted == True:
                    break
            

            if proofcompleted == False:
                return "incomplete"
            else:
                newassumptionstext = copy.deepcopy(assumptionstext)
                for i in range(len(newassumptionstext)):
                    newassumptionstext[i][0].insert(0, str(i+1)+": ")
                    newassumptionstext[i][1].insert(0,'pu')

                proofoftext = proofoftext + newassumptionstext

                if therefore == True:
                    equalObjTexts = [None, None]
                    equalObjCodes = [None, None]
                
                    for i in range(2):
                        objcheck = obj1 if i == 0 else obj2

                        if objcheck[1] == None:
                            equalObjCodes[i] = ['n']
                            equalObjTexts[i] = [objcheck[0]]
                        elif objcheck[1][0][1] == None:
                            equalObjCodes[i] = ['g']
                            equalObjTexts[i] = [objcheck[1][0][0]]
                        else:
                            equalObjCodes[i] = [['g','+1'],'n']
                            equalObjTexts[i] = [objcheck[1][0][0] , objcheck[1][0][1]]

                    proofoftext += [[['------'],['spacer']]]
                    proofoftext += [[['Therefore']+equalObjTexts[0]+['is']+equalObjTexts[1], ['adv']+equalObjCodes[0]+['is']+equalObjCodes[1]]]

                return proofoftext, assumptionstext, reasoningtext
        




        def checkequals(obj, matchobj = None):
            if obj[0] != None:
                type = "noun"
            else:
                type = "verb"
         
            equalities = []
            equal = False
            word = obj[0] if type == "noun" else obj[1][0][0]
            wordstocheck = [obj]
            checkin = None
            waytoproof = []

            if type == "noun":
                checkin = Ndefinitions
            elif type == "verb":
                checkin = Vdefinitions

                if obj[1][0][1] != None:
                    vvequals, equalv, waytoproofVerb, *rest = checkequals([None, [[obj[1][0][0], None]]])
                    vnequals, equaln, waytoproofNoun, *rest = checkequals([obj[1][0][1], None])
                

                    if vnequals not in [None, []]:
                        vnequals.append([obj[1][0][1],None])
                        for equalNoun in vnequals:

                            appendval = [None, [[obj[1][0][0], equalNoun[0]]]]
                            if appendval not in wordstocheck+equalities:
                                if waytoproof == []:
                                    waytoproof.append([])
                                waytoproof[-1].append([obj, appendval])
                                if appendval == matchobj:
                                    equal = True
                                    break

                                prooftextnow, assumptionstext, *rest = prooftextcreator([obj[1][0][1], None], equalNoun, waytoproofNoun)
                                waytoproof[-1][-1].append(assumptionstext)

                            
                                wordstocheck.append(appendval)
                                equalities.append(appendval)

                        if vvequals not in [None, []] and equal == False:
                            for equalNoun in vnequals:
                                for equalVerb in vvequals:
                                    if equalVerb != [None, [[obj[1][0][0], None]]]  and not (equalVerb[1][0][1] != None and len(equalVerb[1][0]) == 2):
                                        appendval = [None, [[equalVerb[1][0][0], equalNoun[0]]]]
                                        if appendval not in wordstocheck+equalities:
                                            if waytoproof == []:
                                                waytoproof.append([])
                                            waytoproof[-1].append([obj, appendval])

                                            if equalNoun == [obj[1][0][1],None]:
                                                prooftextnow, assumptionstext, *rest = prooftextcreator([None, [[obj[1][0][0], None]]], equalVerb, waytoproofVerb)
                                                waytoproof[-1][-1].append(assumptionstext)

                                            if appendval == matchobj:
                                                equal = True
                                                break
                                        
                                            wordstocheck.append(appendval)
                                            equalities.append(appendval)
                                    elif (equalVerb[1][0][1] != None and len(equalVerb[1][0]) == 2):
                                        return "cant exist"
                                if equal == True:
                                    break
                


        
            while len(wordstocheck) > 0 and equal == False:
                wlistcopy = wordstocheck[:]
                wordstocheck = []
                waytoproof.append([])

            
                for i, equalObjCheck in enumerate(wlistcopy):
                    checkword = equalObjCheck[0] if type == "noun" else equalObjCheck[1][0][0]

                    if matchobj != None and equalObjCheck == matchobj:
                        equal = True
                        break

                    if checkword in checkin and (equalObjCheck[1] == None if type == "noun" else (equalObjCheck[1][0][1] == None)):
                        valuecheckfor = checkin[checkword] if type == "noun" else checkin[checkword][0]
                    
                        appendif = [valuecheckfor, None] if type == "noun" else [None, [[valuecheckfor, checkin[checkword][1]]]]
                    
                        if appendif not in equalities and appendif != obj:

                            waytoproof[-1].append([equalObjCheck, appendif])
                            if appendif == matchobj:
                                equal = True
                                break
                            wordstocheck.append(appendif)
                            equalities.append(appendif)


                    
                
                    for defWord, defResultObj in checkin.items():
                        if type != "noun":
                            #print(str(v2))
                            pass
                        Realv2 = defResultObj if type == "noun" else defResultObj[0]
                        appendif = [defWord, None] if type == "noun" else [None, [[defWord, None ]]]

                        if not (type == "verb" and equalObjCheck[1][0][1] != None) and (Realv2 == checkword) and (appendif not in equalities and appendif != obj):
                            addit = False
                            if (type == "verb" and defResultObj[1] ==equalObjCheck[1][0][1]) or type == "noun":
                                addit = True
                            if addit == True:
                                waytoproof[-1].append([appendif, equalObjCheck])
                                if appendif == matchobj:
                                    equal = True
                                    break
                                wordstocheck.append(appendif)
                                equalities.append(appendif)


                        
                        elif (type == "verb" and equalObjCheck[1][0][1] != None) and (defResultObj == equalObjCheck[1][0]) and appendif not in equalities and appendif != obj:


                            waytoproof[-1].append([appendif, equalObjCheck])
                            if appendif == matchobj:
                                equal = True
                                break
                            wordstocheck.append(appendif)
                            equalities.append(appendif)
                            print("V IS THIS " +str(equalObjCheck) + " AND V2 IS THIS "+str(defResultObj))
                
                    if equal == True:
                        break

                if equal == True:
                    break
            
                for i in range(len(wordstocheck)):
                    equalObjCheck = wordstocheck[i]
                    if type == "verb" and equalObjCheck[1][0][1] != None:
                        v1equals, *rest = checkequals([None, [[equalObjCheck[1][0][0], None]]])
                        vnequals, *rest = checkequals([equalObjCheck[1][0][1], None])

                        if vnequals not in [None, []]:
                            for equalNoun in vnequals:
                                appendval = [None, [[equalObjCheck[1][0][0], equalNoun[0]]]]
                                if appendval not in wordstocheck+equalities:
                                    waytoproof[-1].append([equalObjCheck,appendval ])
                                    if appendval == matchobj:
                                        equal = True
                                        break
                                    wordstocheck.append(appendval)
                                    equalities.append(appendval)
                            if equal == True:
                                break

                            if v1equals not in [None, []]:
                                for equalNoun in vnequals:
                                    for equalVerb in v1equals:

                                        if equalVerb != [None, [[equalObjCheck[1][0][0], None]]] and not (equalVerb[1][0][1] != None and len(equalVerb[1][0]) == 2):
                                            appendval = [None, [[equalVerb[1][0][0], equalNoun[0]]]]
                                            if appendval not in wordstocheck+equalities:
                                                waytoproof[-1].append([equalObjCheck,appendval ])
                                                if appendval == matchobj:
                                                    equal = True
                                                    break
                                                wordstocheck.append(appendval)
                                                equalities.append(appendval)

                                        elif (equalVerb[1][0][1] != None and len(equalVerb[1][0]) == 2):
                                            return "cant exist"
                                    if equal == True:
                                        break
            
                if waytoproof[-1] == []:
                    waytoproof.pop()
            
            
                
                
            proofoftext = []

            if equal == True:

                proofoftext, *rest = prooftextcreator(obj, matchobj, waytoproof, True, True)

            return equalities, equal, waytoproof, proofoftext

        try:
            if doc is None:
                answer = build_question_help_answer()
            elif quelist[0] == "is" and len(quelist) > 2: 
    
                Objects = [None,None]
                qlistwtypes = None
                BStartIndex = None
                endresult = None
    
                if len(quelist) == 3:
                    qlistwtypes = [quelist, ['v']]
                    qlistwtypes[0][0] = 'Is'
    
                    for i in range(1,3):
    
                        if doc[i].pos_ == "VERB" and ("Ger" in doc[i].morph.get("VerbForm") or ("Pres" in doc[i].morph.get("Tense") and "Part" in doc[i].morph.get("VerbForm"))):
                            Objects[i-1] = [None,[[doc[i].text, None]]]
                            qlistwtypes[1].append('g')
                        else:
                            Objects[i-1] = [quelist[i],None]
                            qlistwtypes[1].append('n')
                
                else:
                
                
                
                    for i,v in enumerate(reversed(quelist)):
                        reali = len(quelist) - 1 - i
                        if doc[reali].pos_ == "VERB" and ("Ger" in doc[reali].morph.get("VerbForm") or ("Pres" in doc[reali].morph.get("Tense") and "Part" in doc[reali].morph.get("VerbForm"))):
                            cantexist = False
                            if len(quelist) - 1 > reali:
                                print("THIS HAPPENED FOR "+v)
                                checkexist = checkequals([None, [[quelist[reali], quelist[reali+1]]]])
                                if checkexist != None and checkexist == "cant exist":
                                    cantexist = True
    
                            if cantexist == False and reali > 1:
                                print("THIS STOPS IT U WONT SEE ME :3")
                                BStartIndex = reali
                                break
                        
                            elif cantexist == False and reali == 1:
                                VBStartIndex, CAWords, CBWords, fullcompound = checkcompounds(2, len(quelist)-1)
                                if len(CAWords) == 0 and len(CBWords) == 0:
                                    BStartIndex = 2
                                elif fullcompound == False:
                                    BStartIndex = VBStartIndex
                                elif fullcompound == True:
                                    rint = random.randint(0,1)
                                    if rint == 0:
                                        BStartIndex = 2
                                    else:
                                        BStartIndex = VBStartIndex
                                print("1 THAT DIDNT HAPPEN BUT HERE IS TESTS -> "+str(reali)+" "+str(cantexist)+" "+v)
                                break
                            else:
                                print("2 THAT DIDNT HAPPEN BUT HERE IS TESTS -> "+str(reali)+" "+str(cantexist))
                        else:
                            print("DIDNT DETECT VERB FOR "+v)
    
    
    
    
    
                    if BStartIndex == None:
                        VBStartIndex, *rest = checkcompounds(1, len(quelist)-1)
                        BStartIndex = VBStartIndex
    
                    qlistwtypes = [['Is'],['v']]
                    for i, v in enumerate(quelist):
                    
                        objno = None
                        starttest = None
                        if i == 0:
                            continue
    
                        if i < BStartIndex:
                            objno = 0
                            starttest = 1
                        else:
                            objno = 1
                            starttest = BStartIndex
    
                        if i == starttest:
                        
                            if doc[i].pos_ == "VERB" and ("Ger" in doc[i].morph.get("VerbForm") or ("Pres" in doc[i].morph.get("Tense") and "Part" in doc[i].morph.get("VerbForm"))):
                                Objects[objno] = [None,[[v,None]]]
                                qlistwtypes[1].append('g')
                            
                            else:
                                Objects[objno] = [v,[]]
                                qlistwtypes[1].append('n')
    
                            qlistwtypes[0].append(v)
    
                        elif Objects[objno][0] != None:
    
                            Objects[objno][0] += " "+v  
                            qlistwtypes[0][-1] += " "+v
    
                        elif Objects[objno][1][0][1] == None:
                            checkexist = checkequals([None, [[quelist[i-1], v]]])
                            if checkexist == None or checkexist != "cant exist":
                                Objects[objno][1][0][1] = v
                                qlistwtypes[0].append(v)
                                qlistwtypes[1][-1] = [qlistwtypes[1][-1], '+1']
                                qlistwtypes[1].append('n')
                                print("CHECKEXIST NOT CANT EXIST WITH "+doc[i].text+" OMG")
                            else:
                                Objects[objno] = [quelist[i-1]+" "+v,None]
                                qlistwtypes[1][-1] = 'n'
                                qlistwtypes[0][-1] = quelist[i-1]+" "+v
    
                        else:
    
                            Objects[objno][1][0][1] += " "+v
                            qlistwtypes[0][-1] += " "+v
    
    
    
    
                if Objects[0][0] != None and Objects[1][0] != None:
    
                    if Objects[0][0] == Objects[1][0]:
                        answer = [[['Assuming','with','data',':-'],['v','prp','n','pu']],[[Objects[0][0].capitalize(),'is',Objects[1][0]],['n','v','n']]]
                        answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is',Objects[1][0]],['v','n','v','n']]]
    
                    elif ( Objects[0][0] in Ndefinitions or Objects[0][0] in Ndefinitions.values() ) and ( Objects[1][0] in Ndefinitions or Objects[1][0] in Ndefinitions.values() ):
                        equal = False
                        q1equalities = [Objects[0][0]]
                        wordstocheck = [Objects[0][0]]
                        waytoproof = []    
                    
                        while len(wordstocheck) > 0 and equal == False:
                            wlistcopy = wordstocheck[:]
                            wordstocheck = []
                            waytoproof.append([])
    
                        
                            for i,nDefWord1 in enumerate(wlistcopy):
                                if equal == True:
                                    break
    
    
                                if nDefWord1 in Ndefinitions:
                                    if Ndefinitions[nDefWord1] == Objects[1][0]:
                                        waytoproof[-1].append([nDefWord1, Ndefinitions[nDefWord1]])
                                        equal = True
                                        break
                                    else:
                                        if Ndefinitions[nDefWord1] not in q1equalities:
                                        
                                            wordstocheck.append(Ndefinitions[nDefWord1])
                                            q1equalities.append(Ndefinitions[nDefWord1])
                                            waytoproof[-1].append([nDefWord1, Ndefinitions[nDefWord1]])
                            
                                for nDefWord2, nDefObj2 in Ndefinitions.items():
                                    if nDefObj2 == nDefWord1:
                                        if nDefWord2  == Objects[1][0]:
                                            waytoproof[-1].append([nDefWord2, nDefObj2])
                                            equal = True
                                            break
                                        else:
                                            if nDefWord2 not in q1equalities:
                                                wordstocheck.append(nDefWord2)
                                                q1equalities.append(nDefWord2)
                                                waytoproof[-1].append([nDefWord2, nDefObj2])
    
                    
    
                        if equal == True:
                            proofoftext = []
                            nextconnector = Objects[1][0]
    
                            for proofStepList in reversed(waytoproof):
                                for proofStep in proofStepList:
                                    if nextconnector in (proofStep[0], proofStep[1]):
                                        proofoftext.insert(0, [[proofStep[0].capitalize(),"is",proofStep[1]],["n","v","n"]])
                                    
                                        if nextconnector == proofStep[0]:
                                            nextconnector = proofStep[1]
                                        elif nextconnector == proofStep[1]:
                                            nextconnector = proofStep[0]
                                        break
    
                            answer = [[['Assuming','with','data',':-'],['g','prp','n','pu']]] + proofoftext + [[['------'],['spacer']],[['Therefore',Objects[0][0],'is', Objects[1][0]],['v','n','v','n']]]
                        else:
                            match = random.randint(0,1)
                            if match == 0:
                                answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][0].capitalize(),'is','not',Objects[1][0]],['n','v','adv','n']]]
                                answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is','not',Objects[1][0]],['adv','n','v','adv','n']]]
                            else:
                                answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][0].capitalize(),'is',Objects[1][0]],['n','v','n']]]
                                answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is',Objects[1][0]],['adv','n','v','n']]]
                            answer += [[['THIS WAS 3d one'],['n']]]
    
                    else:
                        match = random.randint(0,1)
                        if match == 0:
                            answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][0],'is','not',Objects[1][0]],['n','v','adv','n']]]
                            answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is','not',Objects[1][0]],['adv' ,'n','v','adv','n']]]
    
                        else:
                            answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][0],'is',Objects[1][0]],['n','v','n']]]
                            answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is',Objects[1][0]],['adv','n','v','n']]]
                        answer += [[['THIS WAS 3d one'],['n']]]
      
                    answer = [[['Assuming','you','mean','"']+qlistwtypes[0]+['"'],[['g','+all'],'pro',['v','+all'],'spu']+qlistwtypes[1]+['pus']],[['------'],['spacer']]]+answer
              
    
                elif Objects[0][0] == None and Objects[1][0] == None:
                    if Objects[0][1][0][1] != None or Objects[1][1][0][1] != None:
    
                        ob0equalitites, equal, waytoproof, prooftext  = checkequals(Objects[0], Objects[1])
    
                    
                        answer += prooftext
                    else:
    
                        if Objects[0][1][0][0] == Objects[1][1][0][0]:
                            answer = [[['Assuming','with','data',':-'],['v','prp','n','pu']],[[Objects[0][0].capitalize(),'is',Objects[1][0]],['n','v','n']]]
                            answer += [[['------'],['spacer']],[['Therefore',Objects[0][0],'is',Objects[1][0]],['v','n','v','n']]]
    
                        elif ( Objects[0][1][0][0] in Vdefinitions or any(v[0] == Objects[0][1][0][0] for v in Vdefinitions.values()) ) and ( Objects[1][1][0][0] in Vdefinitions or any(v[0] == Objects[1][1][0][0] for v in Vdefinitions.values()) ):
                            equal = False
                            q1equalities = [Objects[0][1][0][0]]
                            wordstocheck = [Objects[0][1][0][0]]
                            waytoproof = []    
                        
                            while len(wordstocheck) > 0 and equal == False:
                                wlistcopy = wordstocheck[:]
                                wordstocheck = []
                                waytoproof.append([])
    
                            
                                for i,v in enumerate(wlistcopy):
                                    if equal == True:
                                        break
    
    
                                    if v in Vdefinitions:
                                        if Vdefinitions[v][0] == Objects[1][1][0][0]:
                                            waytoproof[-1].append([v, Vdefinitions[v][0]])
                                            equal = True
                                            break
                                        else:
                                            if Vdefinitions[v][0] not in q1equalities:
                                            
                                                wordstocheck.append(Vdefinitions[v][0])
                                                q1equalities.append(Vdefinitions[v][0])
                                                waytoproof[-1].append([v, Vdefinitions[v][0]])
                                
                                    for i2, v2 in Vdefinitions.items():
                                        if v2[0] == v:
                                            if i2  == Objects[1][1][0][0]:
                                                waytoproof[-1].append([i2, v2[0]])
                                                equal = True
                                                break
                                            else:
                                                if i2 not in q1equalities:
                                                    wordstocheck.append(i2)
                                                    q1equalities.append(i2)
                                                    waytoproof[-1].append([i2, v2[0]])
    
                        
                        
                            if equal == True:
                                proofoftext = []
                                nextconnector = Objects[1][1][0][0]
    
                                for proofStepList in reversed(waytoproof):
                                    for proofStep in proofStepList:
                                        if nextconnector in (proofStep[0], proofStep[1]):
                                            proofoftext.insert(0, [[proofStep[0].capitalize(),"is",proofStep[1]],["g","v","g"]])
                                        
                                            if nextconnector == proofStep[0]:
                                                nextconnector = proofStep[1]
                                            elif nextconnector == proofStep[1]:
                                                nextconnector = proofStep[0]
                                            break
    
    
                                answer = [[['Assuming','with','data',':-'],['g','prp','n','pu']]] + proofoftext + [[['------'],['spacer']],[['Therefore',Objects[0][1][0][0],'is', Objects[1][1][0][0]],['v','n','v','n']]]
                            else:
                                match = random.randint(0,1)
                                if match == 0:
                                    answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][1][0][0].capitalize(),'is','not',Objects[1][1][0][0]],['g','v','adv','g']]]
                                    answer += [[['------'],['spacer']],[['Therefore',Objects[0][1][0][0],'is','not',Objects[1][1][0][0]],['adv','g','v','adv','g']]]
                                else:
                                    answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][1][0][0].capitalize(),'is',Objects[1][1][0][0]],['g','v','g']]]
                                    answer += [[['------'],['spacer']],[['Therefore',Objects[0][1][0][0],'is',Objects[1][1][0][0]],['adv','g','v','g']]] 
                            answer += [[['THIS WAS 2nd one'],['n']]]
                        else:
                            match = random.randint(0,1)
                            if match == 0:
                                answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][1][0][0].capitalize(),'is','not',Objects[1][1][0][0]],['g','v','adv','g']]]
                                answer += [[['------'],['spacer']],[['Therefore',Objects[0][1][0][0],'is','not',Objects[1][1][0][0]],['adv','g','v','adv','g']]]
                            else:
                                answer = [[['Assuming','without','data',':-'],['g','prp','n','pu']],[[Objects[0][1][0][0].capitalize(),'is',Objects[1][1][0][0]],['g','v','g']]]
                                answer += [[['------'],['spacer']],[['Therefore',Objects[0][1][0][0],'is',Objects[1][1][0][0]],['adv','g','v','g']]] 
                            answer += [[['THIS WAS 1st one'],['n']]]
                            #answer += [[[Objects[0][1][0][0]]+' '+Objects[1][1][0][0]+' '+str(Vdefinitions)],['n']]
                    
    
    
    
                
                    answer = [[['Assuming','you','mean','"']+qlistwtypes[0]+['"'],[['g','+all'],'pro',['v','+all'],'spu']+qlistwtypes[1]+['pus']],[['------'],['spacer']]]+answer
    
                else:
                    objverb = None
                    nounverb = None
                    directobjs = []
                    if Objects[0][0] == None:
                        objverb = Objects[0][1][0][0]
                        nounverb = Objects[1][0]
                        directobjs = [Objects[0][1][0][0], Objects[1][0],'g','n']
                    else:
                        objverb = Objects[1][1][0][0]
                        nounverb = Objects[0][0]
                        directobjs = [Objects[0][0], Objects[1][1][0][0],'n','g']
    
                    answer = [[['Assuming','with','data',':-'],['g','prp','n','pu']],[[objverb.capitalize(),'is','a','gerund'],['g','v','d','n']],[[nounverb.capitalize(),'is','not','a','gerund'],['n','v','adv','d','n']],[['Gerunds','are','not','the','same','as','non','gerunds'],['n','v','adv','d','n','prp','d','n']],[['------'],['spacer']],[['Therefore',directobjs[0],'is not',directobjs[1]],['adv', directobjs[2], 'v', 'adv', directobjs[3]]]]
                
                    #answer = [[[str(   Objects) + "- " + str(qlistwtypes) + '-' + str(BStartIndex)],['n']]]
                    answer = [[['Assuming','you','mean','"']+qlistwtypes[0]+['"'],[['g','+all'],'pro',['v','+all'],'spu']+qlistwtypes[1]+['pus']],[['------'],['spacer']]]+answer
    
                    #answer = [[[str(answer)],['n']]]
                
            
        
            else:
                answer = build_question_help_answer()
            
        
    
    
        except Exception:
            answer = build_question_help_answer()
        if current_user is None:
            active_chat["history"].append([question, answer])
            if active_chat["title"] == "New chat":
                active_chat["title"] = build_chat_title(question)
            save_session_chats(chats, chat_id)
            state = build_state(chats, active_chat)
        else:
            append_db_message(current_user["id"], chat_id, question, answer)
            state = build_user_state(current_user["id"], chat_id)
        if await wants_json():
            return jsonify(state)
        return redirect(url_for("home", chat=state["active_chat_id"]))

