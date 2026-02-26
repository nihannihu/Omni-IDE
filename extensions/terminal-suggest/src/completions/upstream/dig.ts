/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
const completionSpec: Fig.Spec = {
	name: "dig",
	description: "Domain Information Groper",
	subcommands: [
		{
			name: "A",
			description: "Query Domain A Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "MX",
			description: "Query Domain MX Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "CNAME",
			description: "Query Domain CNAME Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "TXT",
			description: "Query Domain TXT Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "NS",
			description: "Query MX Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "SOA",
			description: "Query SOA Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "TTL",
			description: "Query TTL Record",
			options: [
				{
					name: ["+short", ""],
					insertValue: "+short {cursor}",
					description: "Only print meaningful results",
					args: {},
				},
			],
		},
		{
			name: "ANY +noall +answer",
			description: "Query ALL DNS Records",
		},
		{
			name: "+nocomments +noquestion +noauthority +noadditional +nostats",
			description: "Query only answer section",
		},
	],
};

export default completionSpec;