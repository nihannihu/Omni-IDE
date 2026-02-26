/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { IChannel, IServerChannel } from '../../../base/parts/ipc/common/ipc.js';

export interface IRemoteService {

	readonly _serviceBrand: undefined;

	getChannel(channelName: string): IChannel;
	registerChannel(channelName: string, channel: IServerChannel<string>): void;
}