/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as vscodeGrammarUpdater from 'vscode-grammar-updater';

vscodeGrammarUpdater.update('microsoft/vscode-mssql', 'extensions/mssql/syntaxes/SQL.plist', './syntaxes/sql.tmLanguage.json', undefined, 'main');