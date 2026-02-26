/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import { IWorkbenchContribution } from '../../../common/contributions.js';
import { McpGatewayToolBrokerChannelName } from '../../../../platform/mcp/common/mcpGateway.js';
import { IRemoteAgentService } from '../../../services/remote/common/remoteAgentService.js';
import { IMcpService } from '../common/mcpTypes.js';
import { McpGatewayToolBrokerChannel } from '../common/mcpGatewayToolBrokerChannel.js';

export class McpGatewayToolBrokerContribution implements IWorkbenchContribution {
	constructor(
		@IRemoteAgentService remoteAgentService: IRemoteAgentService,
		@IMcpService mcpService: IMcpService,
	) {
		remoteAgentService.getConnection()?.registerChannel(McpGatewayToolBrokerChannelName, new McpGatewayToolBrokerChannel(mcpService));
	}
}