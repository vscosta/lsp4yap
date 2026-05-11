# lsp4yap: a lsp for YAP

This package introduces a Python based server that interfaces a LSP client to Prolog. The
Python code is based on the pygls package. The server should be client agnostic. We include here a Visual Code extension based on the pygls examples.

## Setup

### Install Server Dependencies

Open a terminal in the repository's root directory

1. Create a virtual environment
   ```
   python -m venv env
   ```

1. Activate the environment
   ```
   source ./env/bin/activate
   ```

1. Install `pygls`
   ```
   python -m pip install -e .
   ```
1. Install YAP and YAP4PY. Note that you should use the virtual environment from the start. A possible sequence might be:
  2. ensure you have python-dev, numpy-dev and swig.
  3. ensure the  virtual environment is the first path your PATH environment variable).
  4. configure, usually `cd build ; cmake -DCMAKE_INSTALL_PREFIX=/my/favorite/place _-DCMAKE_BUILD_TYPE=Debug"
  5, `make install`
  6. `pip install packages/python/yap4py`



### Install Client Dependencies

Open terminal in the same directory as this file and execute following commands:

1. Install node dependencies

   ```
   npm install --no-save
   ```
1. Compile the extension

   ```
   npm run compile
   ```
   Alternatively you can run `npm run watch` if you are going to be actively working on the extension itself.


### Install Server in .emacs

We shall use EGLOT, the FSF supported Emacs client.

1. Either use M-x eglot to activate eglot on need or

2. "Install the following code in the ~/.emacs"
```
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '(prolog-mode . ("/home/vsc/venv/bin/python" "/home/vsc/github/lsp4yap/yap.py"))))

(add-hook 'prolog-mode-hook 'eglot-ensure)


(setq auto-mode-alist (append '(("\\.pl\\'" . prolog-mode)
                                 ("\\.yap\\'" . prolog-mode))
                                auto-mode-alist))
```
3. Your Enacs should be 29 or above; also check the path

4. check the *EGLOT...


## Configuration

By default, the `pygls-playground` extension is configured to run the example `code_actions.py` server which you can find in the `examples/servers` folder of this repository.
(For best results, try opening the `examples/servers/workspace/sums.txt` file).

However, the `.vscode/settings.json` file in this repository can be used alter this and more.
### Selecting documents

Language servers typically specialise in a relatively small number of file types, so a client will only ask a server about documents

The `code_actions.py` example is intended to be used with `plaintext` files (e.g. the provided `sums.txt` file). To use a server with different file types you can modify the `pygls.client.documentSelector` option

For example to use a server with `json` files:

```
"pygls.client.documentSelector": [
    {
        "scheme": "file",
        "language": "json"
    },
],
```

You can find the full list of known language identifiers [here](https://code.visualstudio.com/docs/languages/identifiers#_known-language-identifiers).

See the [LSP Specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentFilter) for details on all the available options that can be passed to the `pygls.client.documentSelector` option.

### Debugging the server

To debug the language server set the `pygls.server.debug` option to `true`.
The server should be restarted and the debugger connect automatically.

You can control the host and port that the debugger uses through the `pygls.server.debugHost` and `pygls.server.debugPort` options.
