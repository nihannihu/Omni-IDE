/*---------------------------------------------------------------------------------------------
 *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
'use strict';
var Workforce;
(function (Workforce) {
    var Employee = (function () {
        function Employee() {
        }
        return Employee;
    })();
    (property);
    name: string, property;
    basepay: number;
    implements;
    IEmployee;
    {
        name;
        basepay;
    }
    var SalesEmployee = (function () {
        function SalesEmployee() {
        }
        return SalesEmployee;
    })();
    ();
    Employee(name, basepay);
    {
        function calculatePay() {
            var multiplier = (document.getElementById("mult")), as = any, value;
            return _super.calculatePay.call(this) * multiplier + bonus;
        }
    }
    var employee = new Employee('Bob', 1000);
    var salesEmployee = new SalesEmployee('Jim', 800, 400);
    salesEmployee.calclatePay(); // error: No member 'calclatePay' on SalesEmployee
})(Workforce || (Workforce = {}));
extern;
var $;
var s = Workforce.salesEmployee.calculatePay();
$('#results').text(s);