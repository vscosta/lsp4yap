############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
"""This implements the publish model of diagnostics.

The original and most widely supported model of diagnostics in LSP, the publish model
allows the server to update the client whenever it is ready.
Unlike the push-model however, there is no way for the client to help the server
prioritize which documents it should be computing the diagnostics for.

This server scans a document for sums e.g. ``1 + 2 = 3``, highlighting any that are
either missing answers (warnings) or incorrect (errors).
"""
import logging
from lsprotocol import types
import uuid

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

import sys

from collections import namedtuple
from yap4py.yapi import Engine, EngineArgs

add_dir = namedtuple("add_dir", "ls uri")
validate_text = namedtuple("validate_text", "uri source")
complete = namedtuple("complete","prefix")
open_uri = namedtuple("open_uri","uri")
pred_def = namedtuple("pred_def","ls word" )
highlight_uri = namedtuple("highlight_uri", "ls uri data")

        
eargs = EngineArgs()

def start_yap():
    eargs.jupyter = True
    try:
        engine = Engine( eargs)
        engine.load_library("lsp")
    except Exception:
        print("bad load")
        engine = None
    return engine       


class YAPServer(LanguageServer):
    """Language server demonstrating "push-model" diagnostics."""

    CMD_PROGRESS = "progress"
    CMD_REGISTER_COMPLETIONS = 
    CMD_SHOW_CONFIGURATION_ASYNC = "showConfigurationAsync"
    CMD_SHOW_CONFIGURATION_CALLBACK = "showConfigurationCallback"
    CMD_SHOW_CONFIGURATION_THREAD = "showConfigurationThread"
    CMD_UNREGISTER_COMPLETIONS =
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diagnostics = {}
    
    def new_message(self, message):
        print(message)
        engine.data += [message]
    
    def validate(self, document: TextDocument):
        """Validates prolog file."""
        diagnostics = []
        uri = document.uri
        data = engine.fun(validate_text(uri,document.source))
        # # TODO: Determine if your linter reports line numbers starting at 1 (True) or 0(False).
        # line_at_1 = True
        # # TODO: Determine if your linter reports column numbers starting at 1 (True) or0 (False).
        # column_at_1 = False
        # line_offset = 1 if line_at_1 else 0
        # col_offset = 1 if column_at_1 else 0
        diagnostics = []
        errs = data
        if errs:
            for (sev,msg,i0,j0,i1,j1) in errs:
                #idx -= 1
                if sev == "warning":
                    sev=types.DiagnosticSeverity.Warning
                else:
                    sev=types.DiagnosticSeverity.Error
                location=types.Range(
                    start=types.Position(line=i0-1, character=j0-1),
                    end=types.Position(line=i1-1, character= j1-1)
                )
                diagnostics.append(
                    types.Diagnostic(
                        message  = msg,
                        severity=types.DiagnosticSeverity.Warning,
                        range = location
                    )
                )
        self.diagnostics[document.uri] = (document.version,diagnostics)
            
class YAPEnv():
    def __init__(self):
        self.data=[]
        self.engine = start_yap()
        self.server =  YAPServer("yap-server", "v1")
        
env = YAPEnv()
server = env.server
engine = env.engine
data = env.data


@server.feature(types.TEXT_DOCUMENT_COMPLETION,types.CompletionOptions(trigger_characters=['\t']))
def completions(ls: YAPServer, params: types.Optional[types.CompletionParams] = None) -> types.CompletionList:
    """Returns completion items."""
    ls.items = []
    document = ls.workspace.get_text_document(params.text_document.uri)
    current_line = document.lines[params.position.line]
    i = col = params.position.character
    prefix = current_line[:params.position.character]
    while i > 0:
        i-=1
        if prefix[i].isalnum():
            continue
        if  prefix[i] == '_':
            continue
        #if i>1 and prefix[i-1:i+1] == "'":
        #    continue
    if i==col:
        return []
    try:
        ls.items = engine.fun(complete(current_line[i:col]))
    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')                       
    return types.CompletionList(
        is_incomplete=True,
        items=[types.CompletionItem(label=i) for i in ls.items]
    )



@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: YAPServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.validate(doc)
    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                version=version,
                diagnostics=diagnostics,
            )
        )



@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: YAPServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.validate(doc)
    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                version=version,
                diagnostics=diagnostics,
            )
        )

document_refs = namedtuple("pred_refs","uri line position")

file_symbols = namedtuple("file_symbols", "uri")

@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: YAPServer, params: types.DocumentSymbolParams):
    """Return all the symbolsb defined in the given document."""
    uri = params.text_document.uri
    results = [ types.DocumentSymbol(
            name=name,
            kind=types.SymbolKind.Class,
            range=types.Range(
                start=types.Position(line=line-1, character=0),
                end=types.Position(line=line, character=0)  
            ),
            selection_range=types.Range(
                start=types.Position(line=line-1, character=0),
                end=types.Position(line=line-1, character=len(name))
            ),
            children=[]
    ) for  (name,line) in engine.fun(file_symbols(uri)) ]
    return results

workspace_symbols = namedtuple("workspace_symbols", "")

@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(ls: YAPServer, params: types.DocumentSymbolParams):
    """Return all the symbols defined in the given document."""
    symbols = engine.fun(workspace_symbols())
    results = [ 
            types.DocumentSymbol(
                name=name,
                kind=types.SymbolKind.Class,
                uri=uri,
                range=types.Range(
                    start=types.Position(line=line-1, character=0),
                    end=types.Position(line=line, character=0),
            )
            #selection_range=range_,
            #children=[],
        )for (name,line,uri) in symbols ]
    return results

symbol_at = namedtuple("symbol_at", "line pos")
definition = namedtuple("definition", "line column")

@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: YAPServer, params: types.TypeDefinitionParams):
    """Jump to an object's definition."""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    line = doc.lines[params.position.line]
    v = engine.fun(definition(line, params.position.character))
    print("v:"+str(v),file=sys.stderr)
    (def_uri, def_line, _, def_length) = v
    return types.Location(uri=def_uri,
            range=types.Range(
                start=types.Position(line=def_line, character=0),
                end=types.Position(line=def_line, character=def_length),
            )
                          )

refs = namedtuple("refs", "word")

@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(ls: YAPServer, params: types.ReferenceParams):
    """Find references of an object."""
    URI = params.text_document.uri
    doc =ls.workspace.get_text_document(URI)
    line = doc.lines[params.position.line]
    items = engine.fun(line, parameteres.position.character)
    print(items )
    if items == []:
        return []
    references = [types.Location(range=types.Range(start=types.Position(line=l-1, character=0),
                                            end=types.Position(line=l-1, character=0)),
                                            uri="file://"+F) for (F, l) in items]
    return references

@server.command("registerCompletions")
async def register_completions(ls: YAPServer, *args):
    """Register completions method on the client."""
    params = types.RegistrationParams(
        registrations=[
            types.Registration(
                id=str(uuid.uuid4()),
                method=types.TEXT_DOCUMENT_COMPLETION,
                register_options={"triggerCharacters": "[':']"},
            )
        ]

    )

    try:
        await ls.client_register_capability_async(params)
        ls.window_show_message(
            types.ShowMessageParams(
                message="Successfully registered completions method",
                type=types.MessageType.Info,
            ),
        )
    except Exception:
        ls.window_show_message(
            types.ShowMessageParams(
                message="Error happened during completions registration.",
                type=types.MessageType.Error,
            ),
        )


@server.command("unregisterCompletions")
async def unregister_completions(ls: YAPServer, *args):
    """Unregister completions method on the client."""
    params = types.UnregistrationParams(
        unregisterations=[
            types.Unregistration(
                id=str(uuid.uuid4()),
                method=types.TEXT_DOCUMENT_COMPLETION,
            ),
        ],
    )

    try:
        await ls.client_unregister_capability_async(params)
        ls.window_show_message(
            types.ShowMessageParams(
                message="Successfully unregistered completions method",
                type=types.MessageType.Info,
            ),
        )
    except Exception:
        ls.window_show_message(
            types.ShowMessageParams(
                message="Error happened during completions unregistration.",
                type=types.MessageType.Error,
            ),
        )



    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
