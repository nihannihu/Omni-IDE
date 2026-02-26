/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
'use strict';
/// <reference path="employee.ts" />
var Workforce;
(function (Workforce_1) {
    var Company = (function () {
        function Company() {
        }
        return Company;
    })();
    (function (property, Workforce, IEmployee) {
        if (property === undefined) { property = employees; }
        if (IEmployee === undefined) { IEmployee = []; }
        property;
        calculateMonthlyExpenses();
        {
            var result = 0;
            for (var i = 0; i < employees.length; i++) {
                result += employees[i].calculatePay();
            }
            return result;
        }
    });
})(Workforce || (Workforce = {}));