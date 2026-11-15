# Security and safety reporting

## Software vulnerabilities

Please report vulnerabilities privately using GitHub's "Report a vulnerability" feature on
this repository (Security → Advisories) rather than a public issue. Include affected files,
a reproduction and the impact you expect. Only the `main` branch is supported.

## Safety-relevant defects

HARVEST-X is intended to control a machine with a powered blade. Defects that could cause
unintended motion, bypass an interlock, weaken e-stop or watchdog behaviour, or mis-report a
safety state are treated as security issues and should be reported the same way.

## Scope notes

- No hardware has been built from this repository yet; no safety function has been validated.
- The design is a research prototype. It is not certified to any machinery-safety or
  functional-safety standard and must not be operated unattended or near untrained persons.
- Never commit credentials, network addresses of lab equipment or personal data.
