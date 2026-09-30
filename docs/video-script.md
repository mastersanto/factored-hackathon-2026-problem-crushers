# Video script: at most 3 minutes

- **Target**: 2:45, to leave margin.
- **Recording**: the live demo at the deployed URL, with the browser at 1280 px wide.
- **Screen**: the customer chat, with the workflow trace on the right, plus the **Especialista** tab.
- **Voice**: Spanish or English, the team's choice. The on-screen text stays in Spanish or Portuguese, as the app is.
- **Before recording**: open the URL once to wake the app, since it scales to zero.

| Time | Screen | Voice-over (short sentences) |
|---|---|---|
| 0:00-0:15 | Title slide or the app header | "In LATAM Bank's data, unrecognized and wrongful charges are 36.5% of all complaints. They take a median of 15 days to resolve, and 1 in 5 misses its deadline. We built *Explica este cargo*: dispute intake that explains a charge from the bank's own records, and hands real cases to a person with everything they need." |
| 0:15-0:50 | Pick an Argentina or Colombia customer; click "No reconozco un cargo…" | "The customer describes the charge in their own words. Code finds it in the customer's own records; the model only interprets the message and rewords the facts. Every sentence is tagged verified, with the record it comes from. Then it asks: do you recognize it now?" Point at the green *verificado* badges and the trace (understand → decide → act → verify). |
| 0:50-1:25 | Click "No fui yo", then "Compartí un código por teléfono" | "If not, it collects what a specialist needs and files the claim. The customer learns their rights for their country and the legal deadline, but never a promised outcome." Switch to **Especialista**: "The specialist gets a structured case: verified facts, card status, whether a code was shared, the legal framework and answer date, a fraud-risk estimate, and open questions. No transcript to read." |
| 1:25-1:50 | Back to chat; click "Me llamaron supuestamente del banco y me pidieron el código…" | "Scam calls drive many of these charges. The customer can ask whether a contact was really the bank. If it asked for a code, it's a scam, always. If they already shared it, the case goes to fraud as urgent." |
| 1:50-2:05 | Type in Portuguese, or click the Portuguese example | "It works the same in Portuguese: understanding, answers, quick replies, and rights." |
| 2:05-2:20 | Click the example naming another customer's ID; then show a vague message | "Safety comes before autonomy. Another customer's data is refused in code, not by the prompt. Vague requests get a question, not a guess." |
| 2:20-2:45 | The evaluation table (slide) | "We evaluated on 180 held-out cases per set, including phrasings the system never saw. With Claude, 96% reach the correct outcome, missed transfers drop from 28 to 2 percent, and there are zero unsafe outcomes, across three runs. The learned fraud estimate catches 37% more frauds than the bank's fixed threshold, at the same precision. Everything is reproducible from the repository." |

**Architecture points to say in passing** (the judges ask for the core decisions):
1. A deterministic state machine decides; models only interpret and reword.
2. Permissions are enforced in the tools, from the session identity.
3. A faithfulness check and a close guard mean a model's mistake cannot close a fraud claim or state a number the records don't have.
4. The assistant runs in rules mode if the model is unavailable.

**Numbers to double-check against `docs/evaluation.md` before recording**: correct outcome, missed transfers, unsafe outcomes, and the fraud catch rate.
