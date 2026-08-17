from __future__ import annotations
import asyncio, json, os, re, time
from pathlib import Path
from typing import Any
import requests
from aiohttp import web

THOR_GAME_LLM_URL = os.environ.get('LLM_GAME_THOR_GAME_LLM_URL', 'http://10.8.0.7:14831').rstrip('/')
THOR_GAME_LLM_MODEL = os.environ.get('LLM_GAME_THOR_GAME_LLM_MODEL', 'qwen3.5-9b-q5-k-m')
CONNECT_TIMEOUT = float(os.environ.get('LLM_GAME_THOR_GAME_LLM_CONNECT_TIMEOUT', '5'))
READ_TIMEOUT = float(os.environ.get('LLM_GAME_THOR_GAME_LLM_READ_TIMEOUT', '150'))
ACTION_READ_TIMEOUT = float(os.environ.get('LLM_GAME_ACTION_READ_TIMEOUT', '40'))
BACKGROUND_LLM_URL = os.environ.get('LLM_GAME_BACKGROUND_LLM_URL', 'http://10.8.0.7:14831').rstrip('/')
BACKGROUND_LLM_MODEL = os.environ.get('LLM_GAME_BACKGROUND_LLM_MODEL', 'qwen3.5-9b-q5-k-m')
BACKGROUND_READ_TIMEOUT = float(os.environ.get('LLM_GAME_BACKGROUND_READ_TIMEOUT', '30'))
GAME_DIR = Path(os.environ.get('LLM_GAME_STATE_DIR', '/data/var/llm_game/game'))
GAME_DIR.mkdir(parents=True, exist_ok=True)
SCENARIO_CACHE = GAME_DIR / 'scenario.json'
ACTION_LOG = GAME_DIR / 'actions.jsonl'
BACKGROUND_LOG = GAME_DIR / 'background.jsonl'
LOCK = asyncio.Lock()
BACKGROUND_LOCK = asyncio.Lock()
ROOM_CONTENT_CAP = int(os.environ.get('LLM_GAME_ROOM_CONTENT_CAP', '12'))
WORLD_ROOM_CAP = int(os.environ.get('LLM_GAME_WORLD_ROOM_CAP', '10'))
ROOM_TOPOLOGY_EXIT_CAP = int(os.environ.get('LLM_GAME_ROOM_TOPOLOGY_EXIT_CAP', '3'))
TOPOLOGY_LOG = GAME_DIR / 'topology.jsonl'
TOPOLOGY_LOCK = asyncio.Lock()

SCENARIO_SYSTEM = (
    'SPRACHE: Sämtlicher für den Spieler sichtbare Inhalt MUSS auf Deutsch sein: Titel, Spielbeschreibung, Prämisse, Auftrag, Einstieg, Raumnamen/-beschreibungen, Objektnamen/-beschreibungen, Zustände als natürlichsprachliche Werte und Affordanzen soweit sinnvoll. Nur JSON-Schlüssel, IDs, Rollen, Shape-Typen, Motion-Typen und technische Tool-Namen bleiben Englisch. '
    'Create the initial semantic state for a persistent top-down RPG. Return compact JSON only. The host provides no story/content templates. You define the player role, environment, object geometry, interaction reaches, physics flags and starting content. '
    'Der Auftrag muss eine klare Motivation, ein überprüfbares Erfolgsziel und mindestens zwei konkrete Informationsquellen/Hinweise in der Startregion besitzen (z.B. NPC, untersuchbares Gerät, Dokument, sichtbarer Zustand). Der opening-Text muss dem Spieler verständlich sagen, wer er ist, was unmittelbar los ist und welches Problem zuerst geklärt werden sollte, ohne die Lösung vorwegzunehmen. '
    'Generate exactly TWO connected rooms: roomA is the starting observed area; roomB is initially unseen and can expand in the background later. Keep this response compact: exactly 4 content entities in roomA and exactly 3 in roomB, plus one reciprocal door/passage in each room. '
    'Every visible entity uses simple 2D shape geometry that is also its exact collider: rect, circle, capsule, cross or polygon. Coordinates use a 1400x860 top-down space; x right/east, y down/south. Put at least two meaningful entities within about 260 units of the player start so the opening view is not empty. '
    'Choose player speed, perception_radius, interaction_reach and speech_reach appropriate to the fiction. Do not make all objects rectangles. Use solid/pushable deliberately. Give NPCs or hazards motion only when it makes sense. '
    'Schema: {"title":string,"game_description":string,"premise":string,"goal":string,"opening":string,"player":{"x":number,"y":number,"shape":shape,"speed":number,"perception_radius":number,"interaction_reach":number,"speech_reach":number,"state":object},"rooms":[{"id":"roomA"|"roomB","name":string,"description":string,"objects":[entity...],"doors":[door]}]}. '
    'entity={"id":string,"name":string,"role":"prop"|"item"|"npc"|"hazard"|"treasure"|"mechanism","description":string,"x":number,"y":number,"shape":shape,"solid":boolean,"pushable":boolean,"interaction_reach":number,"speech_reach":number,"affordances":[string],"state":object,"motion":{"type":"idle"|"wander"|"approach_player"|"flee_player"|"chase_player"|"attack_contact","speed":number,"radius":number,"damage":number}}. '
    'door={"id":string,"name":string,"to":"roomA"|"roomB","x":number,"y":number,"description":string,"shape":shape,"interaction_reach":number}. The two doors must reciprocate. game_description should state who the player is, where they are, important physical/world rules and the kind of reality this game follows; it is supplied to the action LLM every turn.'
)
ACTION_SYSTEM = (
    'SPRACHE: Antworte dem Spieler ausschließlich auf Deutsch. narration und dialogue müssen natürliches, konkretes Deutsch sein. Namen aus dem kanonischen Spielzustand unverändert verwenden. JSON-Schlüssel und Tool-Namen bleiben Englisch. '
    'You are the core semantic RPG engine. The deterministic host handles only geometry, collision/reach, movement integration, persistence and tool validation. YOU decide what the player means, what happens in the fiction, NPC responses, and which persistent state changes are required. '
    'AUFTRAG/INFORMATION: Der Spieler muss jederzeit einen konkreten, verständlichen Auftrag haben. Hinweise dürfen in Raum-/Objektzuständen, untersuchbaren Gegenständen oder NPC-Wissen liegen. Wenn der Spieler nach Ziel, Auftrag, warum, woher weiß ich das, was soll ich tun oder nach einem Hinweis fragt, erkläre konkret den aktuellen Auftrag, bereits bekannte Hinweise und den nächsten plausiblen Informationsweg aus dem kanonischen Zustand; erfinde keine bereits entdeckten Hinweise. '
    'Bei reinen Fragen nach Auftrag, Orientierung oder Informationen ist allowed=true und goal_complete MUSS den bestehenden Zustand goal_complete unverändert widerspiegeln; eine Frage kann niemals allein den Auftrag abschließen. Nenne konkrete Informationsquellen, wenn sie im sichtbaren Zustand oder game_description/goal vorhanden sind. '
    'The user message is always an in-world utterance, question, observation or attempted action. Do not require command syntax. The host supplies the complete local game state: general game_description, goal, room description/bounds, coordinate system, player current/previous coordinates, movement/facing, exact visible/collision shape, speed/reach/state, inventory, every perceived entity with exact shape, absolute and relative coordinates, edge distance, touching/contact, reachability, facing alignment, state, affordances, physics and motion behavior, plus recent conversation/events. USE THIS DATA. '
    'Context representation: visible_environment contains the FULL record for every perceived entity. physical_contacts, interaction_reachable and speech_reachable are arrays of entity IDs referencing those records; nearest_visible, nearest_interactable and best_facing_candidate are single entity IDs. Resolve those IDs against visible_environment. They are compact references, not missing information. '
    'For deictic or terse input such as what is that?, this, it, inspect, interact, use it, hello: resolve physical_contacts first, then nearest_interactable, then best_facing_candidate, then nearest_visible. A touching object or object the player just moved into is highly salient. Do not claim ambiguity when spatial state clearly identifies the likely referent. '
    'OBSERVATION RULE: for questions like what is that?, what is this?, what is X?, inspect, look at it, describe it, or similar observation, identify the resolved entity by its exact name and give useful concrete information from its supplied description plus currently relevant state/motion/role. Do not merely say you inspect/look at/notice it. The narration must tell the player WHAT the thing is or appears to be, what it is doing now, and one salient physical/state detail when available. Do not invent hidden lore that is absent from canonical state. Observation alone uses no tool call. '
    'For physical verbs such as take, pick up, grab, push, pull, open, use or interact, interaction_reachable means the host has ALREADY calculated that the entity is physically within manipulation reach. Do not narrate throwing a hook or merely approaching just to reach an interaction_reachable entity. When exactly one entity is interaction_reachable and the command uses it/this/that, treat that entity as the referent unless its explicit state makes the action impossible. For take/pick up/grab: a reachable role=item or treasure defaults to a successful pickup using inventory_add plus remove_object unless its state explicitly marks it fixed, attached, too_large, non_carryable, or equivalent. Affordance labels such as grapple_target do not override a literal pickup command when the object is already interaction_reachable. If pickup is impossible, explain the concrete state reason instead of pretending to perform it. '
    'Speech is possible only to NPCs in speech_reachable. Physical manipulation is possible only for entities in interaction_reachable. Looking/asking about a visible but distant entity is allowed. '
    'Return one COMPACT wire JSON object in EXACT key order {"n":narration MAX 18 words,"s":speaker or empty,"d":dialogue MAX 24 words or empty,"a":boolean,"i":short intent,"c":[{"t":tool_name,"a":args}],"g":boolean}. Put n first, s second and d third so narration or correctly attributed dialogue can stream immediately. At most 3 calls. Use empty strings and [] when unused. '
    'Available persistent tools are EXACTLY: '
    'set_object {id,patch:{name?,description?,state?,affordances?,shape?,solid?,pushable?,interaction_reach?,speech_reach?}}; '
    'move_object {id,x?,y?,dx?,dy?}; '
    'set_motion {id,type:"idle"|"wander"|"approach_player"|"flee_player"|"chase_player"|"attack_contact",speed?,radius?,damage?,target?}; '
    'remove_object {id}; '
    'create_object {room_id?,object:{id?,name,role,description,x,y,shape,solid,pushable,interaction_reach,speech_reach?,affordances,state,motion?}}; '
    'inventory_add {name}; inventory_remove {name}; set_goal {text}; set_room {room_id?,name?,description?}; set_player {state?,speed?,interaction_reach?,speech_reach?}; create_room {room:{id?,name,description,objects?}}; create_door {from_room_id?,to_room_id,name,description,x,y,shape?,interaction_reach?}; set_actor_plan {id,goal,steps:[{type:"move_to"|"say"|"interact"|"wait"|"set_state",target_id?,x?,y?,speed?,distance?,text?,wait_for_reply?,timeout_seconds?,verb?,target_patch?,target_move?,seconds?,patch?}]}; emit_event {text,speaker?}; schedule_event {delay_seconds,text,speaker?,actor_id?}. '
    'shape is exact visible/collision geometry and may be {type:"rect",width,height}, {type:"circle",radius}, {type:"capsule",width,height}, {type:"cross",width,height,thickness}, or {type:"polygon",points:[[x,y],...]}. '
    'Use tools ONLY when fiction changes persistently. Pure inspection, looking, asking what something is, or ordinary narration MUST NOT rewrite descriptions/state just to restate known facts. Never emit no-op tools: move_object with zero displacement, set_motion identical to current motion, or set_object patches that do not change anything. If an object opens, breaks, falls, changes identity, becomes movable, changes reach, starts fleeing/chasing/attacking, etc., update the corresponding fields. Taking an item normally uses inventory_add plus remove_object. Dropping normally uses inventory_remove plus create_object. '
    'You may set_motion to make characters or objects continue moving after the current turn. The host executes that behavior deterministically from coordinates and collisions. Do not emit arbitrary code. '
    'NPC-LOGIK: NPCs sind handelnde Akteure mit Zielen, Plänen und Gedächtnis im Zustand. Wenn ein NPC ankündigt, zu einem Objekt zu gehen, etwas zu verschieben/öffnen/prüfen, den Spieler anzusprechen oder auf eine Antwort zu warten, darf das NICHT nur Text sein. Verwende set_actor_plan mit konkreten Schritten. move_to bewegt den NPC physisch; interact bewegt/ändert das Zielobjekt erst wenn der NPC es erreicht; say erzeugt tatsächliche Rede und kann auf Antwort warten; wait und set_state bilden mehrstufiges Verhalten. Verwende emit_event für sofort wahrnehmbare Ereignisse und schedule_event für glaubwürdige spätere Ereignisse. Jede angekündigte physische Handlung braucht den passenden persistenten Plan/Tool-Zustand. '
    'NPC dialogue must be concrete and grounded in their known state. If a nearby NPC is addressed, speaker must be its exact name and dialogue must contain what it actually says. For observations, object questions, inspections and non-NPC actions, speaker and dialogue MUST both be empty strings. Generic narration such as you inspect it, you look at it, you interact with it, or nothing happens is unacceptable when canonical description/state provides concrete content. Keep narration consistent with all tool calls; never narrate a persistent change without the tool call that makes it true.'
)
BACKGROUND_EVENT_SYSTEM = (
    'SPRACHE: Alles für den Spieler Sicht-/Hörbare ausschließlich auf Deutsch. JSON-/Tool-Namen bleiben Englisch. '
    'Du bist die Hintergrund-Regie einer persistenten realistischen Spielwelt. Dies ist KEIN Benutzerbefehl. Prüfe den vollständigen sichtbaren Zustand, NPC-Ziele/actor-Pläne, recent_events und das aktuelle Geschehen. '
    'Erzeuge nur dann ein wahrnehmbares Ereignis, wenn es kausal sinnvoll ist: z.B. ein NPC erreicht sein Ziel, spricht den Spieler an, wartet auf Antwort, benutzt/verschiebt ein Objekt, ein bekanntes Gerät macht ein plausibles Geräusch, ein Geruch/Umgebungsdetail hat eine bekannte Quelle, oder eine geplante Konsequenz tritt ein. Kein zufälliges Fantasy-Rauschen und keine bedeutungslosen Meldungen. '
    'Wenn gerade nichts Sinnvolles passiert, gib n,d,s leer und c=[] zurück. Wiederhole keine kürzlich gemeldeten Ereignisse. Ändere physische Zustände niemals nur in Text: benutze Tools. '
    'NPCs brauchen Absichten. Wenn ein NPC etwas vorhat, verwende set_actor_plan. Wenn er zum Spieler geht, soll er einen Grund haben; nach say mit wait_for_reply bleibt er sinnvoll in der Nähe, bis der Spieler antwortet oder die Frist abläuft. '
    'Return exactly the same compact wire JSON schema/order as the action engine: {"n":string,"s":string,"d":string,"a":boolean,"i":string,"c":[tool calls],"g":boolean}. a=true; g darf den Auftrag nicht ohne echte Zustandsgrundlage abschließen.'
)

TOPOLOGY_SYSTEM = (
    'SPRACHE: Alle neu erzeugten spielersichtbaren Namen und Beschreibungen müssen Deutsch sein; technische JSON-Schlüssel/IDs bleiben Englisch. '
    'You expand an UNSEEN top-down RPG frontier. The target room has never been observed. Do not alter any visited room or contradict observed_facts. '
    'Decide whether one additional connected room improves the world. If yes, invent only the new room identity/description and reciprocal passage geometry; room contents will be generated separately. '
    'Coordinates are ENGINE UNITS in a 1400x860 room: x right/east, y down/south. Passage x 60..1340, y 120..740. Passage shape MUST be rect or capsule with width 45..85 and height 70..130. interaction reach 24..50. '
    'Return compact wire JSON: {"c":bool,"r":reason<=12 words,"f":{"n":name,"x":number,"y":number,"d":description<=14 words,"sh":shape,"ir":number},"b":{"n":name,"x":number,"y":number,"d":description<=14 words,"sh":shape,"ir":number},"m":{"n":room_name,"d":room_description<=24 words}}. '
    'When c=false still return f,b,m with empty names/descriptions and safe numeric/shape defaults. The engine assigns canonical room ids. remaining_room_slots is a hard limit.'
)
BACKGROUND_SYSTEM = (
    'SPRACHE: Alle neu erzeugten oder geänderten spielersichtbaren Namen, Beschreibungen und natürlichsprachlichen Zustandswerte müssen Deutsch sein; technische JSON-Schlüssel/IDs bleiben Englisch. '
    'You are the off-screen semantic world generator for a bounded adventure world. You receive one room the player has NEVER observed, its existing semantic objects, the global premise/goal, and an exact number of free object slots. '
    'Add coherent content only inside those free slots. Do not alter facts the player already observed elsewhere and do not solve the game automatically. Prefer concrete useful things: environmental props, clues, mechanisms, minor hazards, creatures/NPCs, tools, containers, remains, inscriptions, sounds with a source, etc. '
    'New content should interconnect with existing objects and the global goal where sensible. observed_facts contains concrete facts already established in places the player has seen, including named objects and their states; use those facts and never contradict them. Make NPCs concrete: give them useful practical knowledge or motives rather than vague riddle-only behavior. Never make access to a locked target require an item that is itself only obtainable from inside that same locked target. If an already-observed key/tool plausibly belongs to a lock or mechanism, prefer connecting those facts consistently. '
    'Return JSON only. Schema: {"room_description":string,"additions":[{"name":string,"role":"prop"|"item"|"npc"|"hazard"|"treasure"|"mechanism","x":number,"y":number,"solid":boolean,"pushable":boolean,"description":string,"shape":object,"interaction_reach":number,"speech_reach":number,"affordances":[string],"state":object,"motion":object}],"updates":[{"id":string,"state":object,"description":string,"affordances":[string]}]}. '
    'Never return more additions than free_slots. If free_slots is zero, additions MUST be empty but useful updates to existing unseen semantic objects are still allowed. Coordinates x 180..1200, y 160..700. Every addition must include shape and interaction_reach; NPCs also need speech_reach. Use motion only if ongoing movement is meaningful. Existing object ids in updates must exactly match supplied ids.'
)

def _json_response(payload: dict[str, Any], status: int = 200) -> web.Response:
    return web.json_response(payload, status=status, headers={'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0','Pragma':'no-cache','Expires':'0'})

def _extract_json(text: str) -> dict[str, Any]:
    raw = str(text or '').strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.I)
    raw = re.sub(r'\s*```$', '', raw)
    try:
        value = json.loads(raw)
        if isinstance(value, dict): return value
    except Exception:
        pass
    a, b = raw.find('{'), raw.rfind('}')
    if a >= 0 and b > a:
        value = json.loads(raw[a:b+1])
        if isinstance(value, dict): return value
    raise ValueError('model did not return a JSON object')

TOPOLOGY_RESPONSE_FORMAT = {
    'type':'json_schema','json_schema':{'name':'topology_wire','strict':True,'schema':{
        'type':'object','properties':{
            'c':{'type':'boolean'},'r':{'type':'string'},
            'f':{'type':'object','properties':{'n':{'type':'string'},'x':{'type':'number'},'y':{'type':'number'},'d':{'type':'string'},'sh':{'type':'object','additionalProperties':True},'ir':{'type':'number'}},'required':['n','x','y','d','sh','ir'],'additionalProperties':False},
            'b':{'type':'object','properties':{'n':{'type':'string'},'x':{'type':'number'},'y':{'type':'number'},'d':{'type':'string'},'sh':{'type':'object','additionalProperties':True},'ir':{'type':'number'}},'required':['n','x','y','d','sh','ir'],'additionalProperties':False},
            'm':{'type':'object','properties':{'n':{'type':'string'},'d':{'type':'string'}},'required':['n','d'],'additionalProperties':False}
        },'required':['c','r','f','b','m'],'additionalProperties':False
    }}
}

def _expand_topology_wire(data: dict[str, Any]) -> dict[str, Any]:
    def door(src: Any) -> dict[str, Any]:
        x=src if isinstance(src,dict) else {}
        return {'name':str(x.get('n') or ''),'x':x.get('x',700),'y':x.get('y',430),'description':str(x.get('d') or ''),
                'shape':x.get('sh') if isinstance(x.get('sh'),dict) else {'type':'rect','width':60,'height':90},'interaction_reach':x.get('ir',30)}
    m=data.get('m') if isinstance(data.get('m'),dict) else {}
    return {'create':bool(data.get('c')),'reason':str(data.get('r') or ''),'door_from':door(data.get('f')),'door_back':door(data.get('b')),
            'room':{'name':str(m.get('n') or ''),'description':str(m.get('d') or ''),'objects':[]}}

ACTION_RESPONSE_FORMAT = {
    'type':'json_schema',
    'json_schema':{
        'name':'game_action_wire','strict':True,
        'schema':{
            'type':'object',
            'properties':{
                'n':{'type':'string'},'s':{'type':'string'},'d':{'type':'string'},
                'a':{'type':'boolean'},'i':{'type':'string'},
                'c':{'type':'array','maxItems':3,'items':{'type':'object','properties':{
                    't':{'type':'string','enum':['set_object','move_object','set_motion','remove_object','create_object','inventory_add','inventory_remove','set_goal','set_room','set_player','create_room','create_door','set_actor_plan','emit_event','schedule_event']},
                    'a':{'type':'object','additionalProperties':True}},'required':['t','a'],'additionalProperties':False}},
                'g':{'type':'boolean'}
            },
            'required':['n','s','d','a','i','c','g'],'additionalProperties':False
        }
    }
}


def _expand_action_wire(data: dict[str, Any]) -> dict[str, Any]:
    calls=[]
    for c in data.get('c') if isinstance(data.get('c'),list) else []:
        if isinstance(c,dict): calls.append({'tool':str(c.get('t') or ''),'args':c.get('a') if isinstance(c.get('a'),dict) else {}})
    return {'allowed':bool(data.get('a')),'intent':str(data.get('i') or ''),'narration':str(data.get('n') or ''),
            'speaker':str(data.get('s') or ''),'dialogue':str(data.get('d') or ''),'tool_calls':calls[:3],'goal_complete':bool(data.get('g'))}


def _chat_endpoint(url: str, model: str, system: str, user: str, max_tokens: int, temperature: float, read_timeout: float, response_format: dict[str, Any] | None = None, on_delta: Any = None) -> dict[str, Any]:
    started = time.monotonic()
    payload={'model':model,'temperature':temperature,'max_tokens':max_tokens,
             'response_format':response_format or {'type':'json_object'},
             'chat_template_kwargs':{'enable_thinking':False},'stream':True,
             'stream_options':{'include_usage':True},
             'messages':[{'role':'system','content':system},{'role':'user','content':user}]}
    response = requests.post(f'{url}/v1/chat/completions',json=payload,timeout=(CONNECT_TIMEOUT,read_timeout),stream=True,
                             headers={'Accept':'text/event-stream'})
    response.raise_for_status()
    chunks=[];usage={};finish_reason=None;first_delta_ms=None
    for raw_line in response.iter_lines(decode_unicode=False,chunk_size=1):
        if not raw_line: continue
        line=raw_line.decode('utf-8','strict').strip()
        if not line.startswith('data:'): continue
        data=line[5:].strip()
        if data=='[DONE]': break
        try: event=json.loads(data)
        except Exception: continue
        if isinstance(event.get('usage'),dict): usage=event['usage']
        choices=event.get('choices') if isinstance(event.get('choices'),list) else []
        if not choices: continue
        choice=choices[0] if isinstance(choices[0],dict) else {}
        if choice.get('finish_reason') is not None: finish_reason=choice.get('finish_reason')
        delta=choice.get('delta') if isinstance(choice.get('delta'),dict) else {}
        content=delta.get('content')
        if isinstance(content,str) and content:
            if first_delta_ms is None: first_delta_ms=int((time.monotonic()-started)*1000)
            chunks.append(content)
            if on_delta is not None: on_delta(content)
    content=''.join(chunks)
    if not content: raise ValueError(f'stream returned no content finish_reason={finish_reason!r}')
    try: parsed=_extract_json(content)
    except Exception as exc:
        tail=content[-600:].replace('\n',' ')
        raise ValueError(f'model JSON parse failed finish_reason={finish_reason!r} chars={len(content)} tail={tail!r}: {exc}') from exc
    return {'data':parsed,'raw':content,'elapsed_ms':int((time.monotonic()-started)*1000),
            'first_delta_ms':first_delta_ms,'usage':usage,'model':model,'finish_reason':finish_reason,'stream':True}

def _chat(system: str, user: str, max_tokens: int, temperature: float, on_delta: Any = None) -> dict[str, Any]:
    return _chat_endpoint(THOR_GAME_LLM_URL,THOR_GAME_LLM_MODEL,system,user,max_tokens,temperature,ACTION_READ_TIMEOUT,ACTION_RESPONSE_FORMAT,on_delta)

def _chat_background(system: str, user: str, max_tokens: int, temperature: float) -> dict[str, Any]:
    return _chat_endpoint(BACKGROUND_LLM_URL,BACKGROUND_LLM_MODEL,system,user,max_tokens,temperature,BACKGROUND_READ_TIMEOUT)

def _chat_topology(system: str, user: str, max_tokens: int, temperature: float) -> dict[str, Any]:
    return _chat_endpoint(BACKGROUND_LLM_URL,BACKGROUND_LLM_MODEL,system,user,max_tokens,temperature,BACKGROUND_READ_TIMEOUT,TOPOLOGY_RESPONSE_FORMAT)

def _cache_record(scenario: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {'generated_ms':int(time.time()*1000),'engine':'thor-background-llm','model':result.get('model',BACKGROUND_LLM_MODEL),
            'scenario':scenario,'elapsed_ms':result.get('elapsed_ms',0),'usage':result.get('usage',{})}

def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    try:
        with path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, separators=(',',':'))+'\n')
    except Exception:
        pass

def _visible_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    vals=state.get('visible_environment') if isinstance(state.get('visible_environment'),list) else []
    return {str(x.get('id','')).strip():x for x in vals if isinstance(x,dict) and str(x.get('id','')).strip()}

def _speech_names(state: dict[str, Any]) -> set[str]:
    vm=_visible_map(state); ids=_subset_ids(state,'speech_reachable')
    return {str(vm[i].get('name','')).strip() for i in ids if i in vm and str(vm[i].get('name','')).strip()}

def _name_key(value: str) -> str:
    import re, unicodedata
    value=unicodedata.normalize('NFKD',str(value or '').casefold())
    value=''.join(ch for ch in value if not unicodedata.combining(ch))
    return ' '.join(re.findall(r'[a-z0-9]+',value))

def _canonical_reachable_speaker(state: dict[str, Any], speaker: str) -> str | None:
    names=sorted(_speech_names(state))
    if not names: return None
    raw=_name_key(speaker)
    if not raw: return None
    keyed=[(name,_name_key(name)) for name in names]
    for name,key in keyed:
        if raw==key: return name
    # Accept natural short forms such as "Herr Krüger" for "Herr Krüger, der Hausmeister".
    matches=[name for name,key in keyed if raw in key or key in raw]
    if len(matches)==1: return matches[0]
    rt=set(raw.split())
    scored=[]
    for name,key in keyed:
        kt=set(key.split()); common=rt & kt
        if common: scored.append((len(common)/max(1,len(rt)),len(common),name))
    scored.sort(reverse=True)
    if scored and scored[0][0]>=0.5 and (len(scored)==1 or scored[0][:2]>scored[1][:2]): return scored[0][2]
    # If exactly one NPC can hear the player, a shortened/translated speaker label cannot make them out of range.
    if len(names)==1: return names[0]
    return None

def _visible_ids(state: dict[str, Any]) -> set[str]:
    return set(_visible_map(state))

def _subset_ids(state: dict[str, Any], key: str) -> set[str]:
    vals=state.get(key) if isinstance(state.get(key),list) else []
    out=set()
    for x in vals:
        if isinstance(x,str) and x.strip(): out.add(x.strip())
        elif isinstance(x,dict) and str(x.get('id','')).strip(): out.add(str(x.get('id','')).strip())
    return out

def _enforce_action_scope(data: dict[str, Any], state: dict[str, Any], action: str, mode: str = 'action') -> dict[str, Any]:
    visible=_visible_ids(state); interaction=_subset_ids(state,'interaction_reachable'); speech=_subset_ids(state,'speech_reachable')
    valid_tools={'set_object','move_object','set_motion','remove_object','create_object','inventory_add','inventory_remove','set_goal','set_room','set_player','create_room','create_door','set_actor_plan','emit_event','schedule_event'}
    calls=[]
    for c in data.get('tool_calls') if isinstance(data.get('tool_calls'),list) else []:
        if not isinstance(c,dict): continue
        tool=str(c.get('tool') or ''); args=c.get('args') if isinstance(c.get('args'),dict) else {}
        if tool not in valid_tools: continue
        oid=str(args.get('id') or '')
        if mode=='background':
            if tool in {'move_object','remove_object','set_object','set_motion','set_actor_plan'} and oid and oid not in visible: continue
        else:
            if tool in {'move_object','remove_object'} and oid not in interaction: continue
            if tool in {'set_object','set_motion','set_actor_plan'} and oid and oid not in (interaction|speech): continue
        if tool=='move_object' and not any(abs(float(args.get(k) or 0))>1e-9 for k in ('dx','dy')) and 'x' not in args and 'y' not in args: continue
        if tool=='create_object':
            rid=str(args.get('room_id') or state.get('current_room',{}).get('id') or '')
            if rid and rid!=str(state.get('current_room',{}).get('id') or ''): continue
        calls.append({'tool':tool,'args':args})
    data['tool_calls']=calls[:16]
    data.pop('mutations',None)
    speaker=str(data.get('speaker') or '').strip(); dialogue=str(data.get('dialogue') or '').strip()
    if dialogue and speaker:
        canonical=_canonical_reachable_speaker(state,speaker)
        if canonical:
            data['speaker']=canonical
        else:
            data['speaker']='';data['dialogue']='';data['tool_calls']=[];data['goal_complete']=False;data['allowed']=False;data['intent']='speech_out_of_range';data['narration']='Deine Worte verhallen, aber niemand in Hörweite antwortet.'
    return data


def _background_consistency(data: dict[str, Any], request_data: dict[str, Any]) -> dict[str, Any]:
    observed = request_data.get('observed_facts') if isinstance(request_data.get('observed_facts'), list) else []
    known_objects=[]
    for fact in observed:
        if not isinstance(fact,dict): continue
        for o in fact.get('objects') if isinstance(fact.get('objects'),list) else []:
            if isinstance(o,dict): known_objects.append(o)
    keys=[o for o in known_objects if ('key' in str(o.get('name','')).lower() or any('unlock' in str(a).lower() for a in (o.get('affordances') or [])))]
    room=request_data.get('room') if isinstance(request_data.get('room'),dict) else {}
    targets=[o for o in (room.get('objects') or []) if isinstance(o,dict) and ('locked' in str(o.get('name','')).lower() or (isinstance(o.get('state'),dict) and o['state'].get('locked') is True))]
    if len(keys)==1 and len(targets)==1:
        key_name=str(keys[0].get('name') or 'key')[:80]
        target_id=str(targets[0].get('id') or '')
        target_name=str(targets[0].get('name') or 'locked object')
        updates=data.get('updates') if isinstance(data.get('updates'),list) else []
        byid={str(u.get('id')):u for u in updates if isinstance(u,dict) and u.get('id')}
        u=byid.setdefault(target_id,{'id':target_id})
        st=u.get('state') if isinstance(u.get('state'),dict) else {}
        st['requires']=key_name; st['locked']=True; u['state']=st
        if target_id not in {str(x.get('id')) for x in updates if isinstance(x,dict)}: updates.append(u)
        # Reconcile any NPC knowledge that mentions the target but is vague/circular.
        for o in (room.get('objects') or []):
            if not isinstance(o,dict) or str(o.get('role'))!='npc': continue
            oid=str(o.get('id') or ''); nu=byid.get(oid)
            if nu is None:
                nu={'id':oid}; updates.append(nu); byid[oid]=nu
            nst=nu.get('state') if isinstance(nu.get('state'),dict) else {}
            nst['knowledge']=f'The {key_name} unlocks the {target_name}. The player can use the key directly on the lock.'
            nu['state']=nst
        data['updates']=updates
    return data

def _next_room_id(existing: set[str]) -> str:
    for i in range(26):
        rid=f'room{chr(ord("A")+i)}'
        if rid not in existing: return rid
    n=1
    while f'room{n}' in existing: n+=1
    return f'room{n}'

def _sanitize_generated_object(raw: dict[str, Any], idx: int, room_id: str) -> dict[str, Any]:
    role=str(raw.get('role') or 'prop')
    if role not in {'prop','item','npc','hazard','treasure','mechanism'}: role='prop'
    def num(v,lo,hi,default):
        try:return max(lo,min(hi,float(v)))
        except Exception:return default
    shape=raw.get('shape') if isinstance(raw.get('shape'),dict) else {'type':'rect','width':48,'height':48}
    motion=raw.get('motion') if isinstance(raw.get('motion'),dict) else {'type':'idle','speed':0,'radius':0,'damage':0}
    return {'id':str(raw.get('id') or f'bg_{room_id}_{int(time.time()*1000)}_{idx}')[:60],
            'name':str(raw.get('name') or f'Object {idx}')[:80],'role':role,
            'x':num(raw.get('x'),80,1320,700),'y':num(raw.get('y'),100,760,430),
            'shape':shape,'solid':bool(raw.get('solid')),'pushable':bool(raw.get('pushable')),
            'interaction_reach':num(raw.get('interaction_reach'),0,180,24),
            'speech_reach':num(raw.get('speech_reach'),0,500,160 if role=='npc' else 0),
            'description':str(raw.get('description') or '')[:600],
            'affordances':[str(x)[:60] for x in (raw.get('affordances') if isinstance(raw.get('affordances'),list) else [])][:12],
            'state':raw.get('state') if isinstance(raw.get('state'),dict) else {},'motion':motion}

async def game_status(request: web.Request) -> web.Response:
    record = None
    try:
        if SCENARIO_CACHE.exists(): record = json.loads(SCENARIO_CACHE.read_text())
    except Exception:
        record = None
    reachable = False
    try:
        r = await asyncio.to_thread(requests.get, f'{THOR_GAME_LLM_URL}/health', timeout=(2,4))
        reachable = bool(r.ok)
    except Exception:
        pass
    return _json_response({'ok':True,'engine':'thor-qwen3.5-9b','model':THOR_GAME_LLM_MODEL,
                           'reachable':reachable,'interactive_model':THOR_GAME_LLM_MODEL,'background_model':BACKGROUND_LLM_MODEL,'scenario_cached':bool(record),'room_cap':WORLD_ROOM_CAP,'room_content_cap':ROOM_CONTENT_CAP,'room_topology_exit_cap':ROOM_TOPOLOGY_EXIT_CAP,'record':record})

async def game_scenario(request: web.Request) -> web.Response:
    try: payload=await request.json()
    except Exception: payload={}
    regenerate=bool(payload.get('regenerate'))
    theme=str(payload.get('theme') or 'Realistische, leicht komische Gegenwartssituation mit klarer Aufgabe; keine Fantasy, keine Magie, keine erfundenen kosmischen Regeln.').strip()[:500]
    if not regenerate and SCENARIO_CACHE.exists():
        try:return _json_response({'ok':True,'cached':True,'record':json.loads(SCENARIO_CACHE.read_text())})
        except Exception:pass
    async with LOCK:
        try:
            outline_prompt=(
                'Erzeuge eine KOMPAKTE, verständliche Spielgrundlage auf Deutsch, zunächst ohne Raumobjekte. Das Setting muss realistisch/alltäglich und leicht komisch sein, mit nachvollziehbarer Ursache-Wirkung. KEINE Fantasy, Magie, Kristallenergie, nicht-euklidischen Welten, Leere, kosmischen Kräfte oder bedeutungslosen Eigennamen. Humor soll aus einer glaubwürdigen peinlichen/chaotischen Situation entstehen. Der Spieler braucht eine konkrete Rolle, ein klares Problem, ein überprüfbares Ziel und erkennbare Informationsquellen. JSON schema: '
                '{"title":string,"game_description":string,"premise":string,"goal":string,"opening":string,'
                '"player":{"x":number,"y":number,"shape":object,"speed":number,"perception_radius":number,"interaction_reach":number,"speech_reach":number,"state":object},'
                '"rooms":[{"id":"roomA"|"roomB","name":string,"description":string,"door":{"id":string,"name":string,"to":"roomA"|"roomB","x":number,"y":number,"description":string,"shape":object,"interaction_reach":number}}]}. '
                'Exactly two rooms, reciprocal doors, player starts in roomA. Shapes are exact visible/collision geometry. Alle spielersichtbaren Texte Deutsch. Engine-Skala 1400x860; player speed 150..230, perception_radius 300..420, interaction_reach 22..48, speech_reach 150..230. Theme: '+theme)
            outline_res=await asyncio.to_thread(_chat_background,'You are a concise RPG world architect. JSON only.',outline_prompt,520,0.25)
            outline=outline_res['data']; rooms=outline.get('rooms') if isinstance(outline.get('rooms'),list) else []
            if {str(r.get('id')) for r in rooms}!={'roomA','roomB'}: raise ValueError('outline must contain roomA and roomB')
            assembled=[]; total_usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}; total_ms=outline_res.get('elapsed_ms',0)
            for k,v in (outline_res.get('usage') or {}).items():
                if isinstance(v,(int,float)): total_usage[k]=total_usage.get(k,0)+v
            for rr in rooms:
                rid=str(rr['id']); count=4 if rid=='roomA' else 3
                content_prompt=(
                    f'Erzeuge für {rid} genau {count} sinnvolle, realistische Entitäten auf Deutsch. Jedes Objekt muss eine erkennbare Funktion für Umgebung, Information, Hindernis, Humor oder Auftrag haben; kein zufälliger Fantasy-Füllstoff. JSON schema: {{"objects":[entity,...]}}. '
                    'entity requires id,name,role,description,x,y,shape,solid,pushable,interaction_reach,speech_reach,affordances,state,motion. '
                    'shape types: rect(width,height), circle(radius), capsule(width,height), cross(width,height,thickness), polygon(points). '
                    'motion type one of idle,wander,approach_player,flee_player,chase_player,attack_contact with speed,radius,damage. '
                    'Coordinates within x 120..1280 y 120..740. Do not duplicate the door. For roomA put at least two entities within 280 units of player start. '
                    f'Game description: {outline.get("game_description","")} Goal: {outline.get("goal","")} Player: {json.dumps(outline.get("player",{}),separators=(",",":"))} '
                    f'Room: {json.dumps(rr,separators=(",",":"))}')
                res=await asyncio.to_thread(_chat_background,'Du erzeugst kompakte, realistische physische Spielobjekte. Alle spielersichtbaren Texte Deutsch. JSON only.',content_prompt,520,0.25)
                objs=res['data'].get('objects') if isinstance(res['data'].get('objects'),list) else []
                if len(objs)!=count: raise ValueError(f'{rid} expected {count} objects, got {len(objs)}')
                room={'id':rid,'name':str(rr.get('name') or rid),'description':str(rr.get('description') or ''),'objects':objs,'doors':[rr.get('door') or {}]}
                assembled.append(room); total_ms+=res.get('elapsed_ms',0)
                for k,v in (res.get('usage') or {}).items():
                    if isinstance(v,(int,float)): total_usage[k]=total_usage.get(k,0)+v
            byid={r['id']:r for r in assembled}
            for r in assembled:
                d=r['doors'][0]
                if d.get('to') not in byid or not any(x.get('to')==r['id'] for x in byid[d.get('to')]['doors']): raise ValueError('doors not reciprocal')
            scenario={k:outline.get(k) for k in ['title','game_description','premise','goal','opening','player']}; scenario['rooms']=assembled
            record={'generated_ms':int(time.time()*1000),'engine':'thor-qwen3.5-9b-staged','model':BACKGROUND_LLM_MODEL,'scenario':scenario,'elapsed_ms':total_ms,'usage':total_usage}
            SCENARIO_CACHE.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
            return _json_response({'ok':True,'cached':False,'record':record})
        except Exception as exc:
            return _json_response({'ok':False,'engine':'thor-qwen3.5-9b-staged','error':f'{exc.__class__.__name__}: {exc}'},502)

async def game_action(request: web.Request) -> web.StreamResponse:
    try: payload = await request.json()
    except Exception: return _json_response({'ok':False,'error':'Ungültige JSON-Anfrage'},400)
    action = str(payload.get('action') or '').strip()[:500]
    if not action: return _json_response({'ok':False,'error':'Leere Aktion'},400)
    state = payload.get('state') if isinstance(payload.get('state'),dict) else {}
    request_id=str(payload.get('request_id') or '')[:100]; attempt=max(1,min(9,int(payload.get('attempt') or 1))); mode='background' if payload.get('mode')=='background' else 'action'
    compact = json.dumps({'action':action,'mode':mode,'state':state},ensure_ascii=False,separators=(',',':'))[:18000]
    started_ms=int(time.time()*1000);loop=asyncio.get_running_loop();queue=asyncio.Queue()
    response=web.StreamResponse(status=200,headers={'Content-Type':'application/x-ndjson; charset=utf-8','Cache-Control':'no-cache, no-store','X-Accel-Buffering':'no'})
    await response.prepare(request)
    async def send(obj: dict[str, Any]) -> None:
        await response.write((json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
    await send({'type':'start','engine':'thor-qwen3.5-9b','model':THOR_GAME_LLM_MODEL,'stream':True,'request_id':request_id,'attempt':attempt,'mode':mode})
    def on_delta(delta: str) -> None:
        loop.call_soon_threadsafe(queue.put_nowait,delta)
    async with LOCK:
        system_prompt=BACKGROUND_EVENT_SYSTEM if mode=='background' else ACTION_SYSTEM
        worker=asyncio.create_task(asyncio.to_thread(_chat,system_prompt,compact,220,0.02,on_delta))
        try:
            while True:
                if worker.done() and queue.empty(): break
                try: delta=await asyncio.wait_for(queue.get(),timeout=0.05)
                except asyncio.TimeoutError: continue
                await send({'type':'delta','delta':delta})
            result=await worker
            data=_enforce_action_scope(_expand_action_wire(result['data']),state,action,mode)
            record={'time_ms':started_ms,'request_id':request_id,'attempt':attempt,'mode':mode,'action':action,'room':state.get('current_room',{}).get('name'),'player':state.get('player'),'inventory':state.get('inventory'),'visible':state.get('visible_environment'),'interaction_reachable':state.get('interaction_reachable'),'speech_reachable':state.get('speech_reachable'),'conversation':state.get('conversation'),'result':data,'elapsed_ms':result['elapsed_ms'],'first_delta_ms':result.get('first_delta_ms'),'usage':result['usage'],'finish_reason':result.get('finish_reason'),'stream':True}
            _append_jsonl(ACTION_LOG,record)
            await send({'type':'final','ok':True,'engine':'thor-qwen3.5-9b','model':THOR_GAME_LLM_MODEL,'elapsed_ms':result['elapsed_ms'],'first_delta_ms':result.get('first_delta_ms'),'result':data,'usage':result['usage']})
        except Exception as exc:
            if not worker.done(): worker.cancel()
            _append_jsonl(ACTION_LOG,{'time_ms':started_ms,'request_id':request_id,'attempt':attempt,'mode':mode,'action':action,'state':state,'error':f'{exc.__class__.__name__}: {exc}','stream':True})
            await send({'type':'error','ok':False,'engine':'thor-qwen3.5-9b','error':f'{exc.__class__.__name__}: {exc}'})
    await response.write_eof()
    return response

async def game_expand(request: web.Request) -> web.Response:
    try: payload=await request.json()
    except Exception: return _json_response({'ok':False,'error':'Ungültige JSON-Anfrage'},400)
    room_state=payload.get('room') if isinstance(payload.get('room'),dict) else {}
    if bool(payload.get('observed')):
        return _json_response({'ok':True,'skipped':'room already observed','result':{'additions':[],'updates':[]}})
    allow_updates=bool(payload.get('allow_updates'))
    existing_objects=room_state.get('objects') if isinstance(room_state.get('objects'),list) else []
    capacity=max(0,ROOM_CONTENT_CAP-len(existing_objects))
    requested=max(0,min(3,int(payload.get('free_slots') or 0)))
    free_slots=min(requested,capacity)
    if not free_slots and not allow_updates:
        return _json_response({'ok':True,'skipped':'room full','result':{'additions':[],'updates':[]}})
    room_id=str(room_state.get('id') or 'room')[:50]
    request_data={'premise':str(payload.get('premise') or '')[:700],'goal':str(payload.get('goal') or '')[:500],
                  'room':room_state,'free_slots':free_slots,
                  'observed_facts':payload.get('observed_facts',[])[:30] if isinstance(payload.get('observed_facts'),list) else []}
    started_ms=int(time.time()*1000)
    async with BACKGROUND_LOCK:
        try:
            result=await asyncio.to_thread(_chat_background,BACKGROUND_SYSTEM,json.dumps(request_data,ensure_ascii=False,separators=(',',':')),180,0.35)
            data=_background_consistency(result['data'],request_data)
            data['additions']=data.get('additions',[])[:free_slots] if isinstance(data.get('additions'),list) else []
            existing={str(o.get('id')) for o in existing_objects if isinstance(o,dict)}
            data['updates']=[u for u in data.get('updates',[]) if isinstance(u,dict) and str(u.get('id')) in existing][:8] if isinstance(data.get('updates'),list) else []
            for i,a in enumerate(data['additions']):
                if isinstance(a,dict) and not a.get('id'): a['id']=f'bg_{room_id}_{started_ms}_{i+1}'
            _append_jsonl(BACKGROUND_LOG,{'time_ms':started_ms,'request':request_data,'result':data,'elapsed_ms':result['elapsed_ms'],'usage':result['usage']})
            return _json_response({'ok':True,'engine':'thor-background-llm','model':result.get('model',BACKGROUND_LLM_MODEL),'elapsed_ms':result['elapsed_ms'],'result':data})
        except Exception as exc:
            _append_jsonl(BACKGROUND_LOG,{'time_ms':started_ms,'request':request_data,'error':f'{exc.__class__.__name__}: {exc}'})
            return _json_response({'ok':False,'error':f'{exc.__class__.__name__}: {exc}'},502)

async def game_topology(request: web.Request) -> web.Response:
    try: payload=await request.json()
    except Exception: return _json_response({'ok':False,'error':'Ungültige JSON-Anfrage'},400)
    if bool(payload.get('target_observed')):
        return _json_response({'ok':True,'skipped':'target already observed','result':{'create':False}})
    target=payload.get('target_room') if isinstance(payload.get('target_room'),dict) else {}
    target_id=str(target.get('id') or '')
    if not target_id:return _json_response({'ok':False,'error':'Zielraum fehlt'},400)
    existing_ids={str(x) for x in (payload.get('existing_room_ids') if isinstance(payload.get('existing_room_ids'),list) else []) if str(x)}
    if target_id not in existing_ids:existing_ids.add(target_id)
    room_count=max(len(existing_ids),int(payload.get('world_room_count') or 0))
    if room_count>=WORLD_ROOM_CAP:
        return _json_response({'ok':True,'skipped':'world room cap','room_count':room_count,'room_cap':WORLD_ROOM_CAP,'result':{'create':False}})
    expansion_count=max(0,int(payload.get('target_topology_expansions') or 0))
    if bool(payload.get('target_topology_closed')) or expansion_count>=ROOM_TOPOLOGY_EXIT_CAP:
        return _json_response({'ok':True,'skipped':'frontier complete','result':{'create':False},'topology_expansions':expansion_count})
    request_data={'premise':str(payload.get('premise') or '')[:900],'goal':str(payload.get('goal') or '')[:600],
                  'world_room_count':room_count,'remaining_room_slots':WORLD_ROOM_CAP-room_count,
                  'target_room':target,'observed_facts':payload.get('observed_facts',[])[:30] if isinstance(payload.get('observed_facts'),list) else []}
    started_ms=int(time.time()*1000)
    async with TOPOLOGY_LOCK:
        try:
            result=await asyncio.to_thread(_chat_topology,TOPOLOGY_SYSTEM,json.dumps(request_data,ensure_ascii=False,separators=(',',':')),140,0.20)
            data=_expand_topology_wire(result['data'])
            create=bool(data.get('create')) and room_count<WORLD_ROOM_CAP
            created_room=None; from_door=None; new_count=expansion_count; closed=False
            if create:
                new_count=expansion_count+1
                rid=_next_room_id(existing_ids)
                rr=data.get('room') if isinstance(data.get('room'),dict) else {}
                raw_objs=rr.get('objects') if isinstance(rr.get('objects'),list) else []
                objs=[_sanitize_generated_object(o,i+1,rid) for i,o in enumerate(raw_objs[:ROOM_CONTENT_CAP]) if isinstance(o,dict)]
                df=data.get('door_from') if isinstance(data.get('door_from'),dict) else {}
                db=data.get('door_back') if isinstance(data.get('door_back'),dict) else {}
                def coord(v,lo,hi,default):
                    try:return max(lo,min(hi,float(v)))
                    except Exception:return default
                from_door={'id':f'door_{target_id}_{rid}','name':str(df.get('name') or f'Durchgang zu {rr.get("name") or rid}')[:90],
                           'to':rid,'x':coord(df.get('x'),80,1320,1320),'y':coord(df.get('y'),100,760,430),
                           'description':str(df.get('description') or '')[:500],'shape':df.get('shape') if isinstance(df.get('shape'),dict) else {'type':'rect','width':60,'height':90},'interaction_reach':coord(df.get('interaction_reach'),24,50,30)}
                back_door={'id':f'door_{rid}_{target_id}','name':str(db.get('name') or f'Durchgang zu {target.get("name") or target_id}')[:90],
                           'to':target_id,'x':coord(db.get('x'),80,1320,80),'y':coord(db.get('y'),100,760,430),
                           'description':str(db.get('description') or '')[:500],'shape':db.get('shape') if isinstance(db.get('shape'),dict) else {'type':'rect','width':60,'height':90},'interaction_reach':coord(db.get('interaction_reach'),24,50,30)}
                created_room={'id':rid,'name':str(rr.get('name') or rid)[:100],'description':str(rr.get('description') or 'An unexplored area.')[:1000],
                              'objects':objs,'doors':[back_door],'topology_expansions':0,'topology_closed':False}
            else:
                closed=True
            record={'time_ms':started_ms,'target_room_id':target_id,'create':create,'created_room':created_room,'door_from':from_door,
                    'model_result':data,'room_count_before':room_count,'room_cap':WORLD_ROOM_CAP,'target_topology_expansions':new_count,
                    'target_topology_closed':closed,'elapsed_ms':result['elapsed_ms'],'usage':result['usage']}
            _append_jsonl(TOPOLOGY_LOG,record)
            return _json_response({'ok':True,'engine':'thor-background-llm','model':result.get('model',BACKGROUND_LLM_MODEL),'elapsed_ms':result['elapsed_ms'],'room_count':room_count+(1 if create else 0),'room_cap':WORLD_ROOM_CAP,
                                   'result':{'create':create,'target_room_id':target_id,'room':created_room,'door_from':from_door,'reason':data.get('reason',''),
                                             'target_topology_expansions':new_count,'target_topology_closed':closed}})
        except Exception as exc:
            _append_jsonl(TOPOLOGY_LOG,{'time_ms':started_ms,'target_room_id':target_id,'error':f'{exc.__class__.__name__}: {exc}'})
            return _json_response({'ok':False,'error':f'{exc.__class__.__name__}: {exc}'},502)

def install_routes(app: web.Application) -> None:
    app.router.add_get('/http/game/status', game_status)
    app.router.add_post('/http/game/scenario', game_scenario)
    app.router.add_post('/http/game/action', game_action)
    app.router.add_post('/http/game/expand', game_expand)
    app.router.add_post('/http/game/topology', game_topology)
