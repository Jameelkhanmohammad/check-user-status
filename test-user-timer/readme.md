# TimerTrigger - Python

The `TimerTrigger` makes it incredibly easy to have your functions executed on a schedule. This sample demonstrates a simple use case of calling your function every hour.

## How it works

For a `TimerTrigger` to work, you provide a schedule in the form of a [cron expression](https://en.wikipedia.org/wiki/Cron#CRON_expression)(See the link for full details). A cron expression is a string with 6 separate expressions which represent a given schedule via patterns. The pattern we use to represent every hour at 0 minutes is `0 0 */1 * * *`. This, in plain text, means: "When seconds is equal to 0, minutes is 0, for hour divisible by 1, day of the month, month, day of the week, or year".

## Learn more

<TODO> Documentation
