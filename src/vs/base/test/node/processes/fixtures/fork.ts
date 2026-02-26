/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as processes from '../../../../node/processes.js';

const sender = processes.createQueuedSender(<any>process);

process.on('message', msg => {
	sender.send(msg);
});

sender.send('ready');