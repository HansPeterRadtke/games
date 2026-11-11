# Practice and round feedback

## Screen and module contract

The typing trainer is an action screen for a player using a physical or touch keyboard. During practice, the player needs to see the next letter, act immediately and tell what counted. At the end of a round, the same player needs to see what they achieved and what they can beat next.

| Priority | Player question | Visible answer or action |
| --- | --- | --- |
| First | What do I type, and how do I start or resume? | The active exercise and primary button fit the initial view. Selected mode, level and ready, active, paused or completed state identify the task. |
| First | Did my letter count? Did I beat a record? | The cursor advances or marks a mistake immediately. A nearby result gives the metric, comparison and gain. A lifetime improvement has the strongest emphasis. |
| First | How far through the exercise am I? | A labeled progress bar and completed/total count. In sequence mode, the round position is beside the exercise. |
| Secondary | Am I getting faster or more accurate, and what is my next target? | Recent scores appear in chronological order on a labeled chart. Choose the statistic and number of comparable rounds. The rolling and lifetime targets remain distinct. |
| On demand | How do I configure practice or inspect individual measurements? | Expand Practice settings or inspect exact round values and practice history. Keep backup actions separate from Start and Pause. |

An unfinished round contributes progress only. Only completed comparable rounds supply round measurements. The one-sample state is a single observation. Missing values have no plotted point. Ties and baselines retain their existing labels. An absent record or a storage failure must have a clear visible explanation. Raw state and development diagnostics have no place on the play screen.

**Metrics.** Sequence time is elapsed active time for the same sequence, in seconds or milliseconds, lower is faster. Other modes use correct characters per five per active minute, higher is faster. Accuracy is correct attempts divided by all attempts, including corrected errors, and higher is better. Recent targets, means, strict improvement, comparison scopes and lifetime retention are defined in the project README. Chart position encodes score on an explicitly labeled linear axis. Exact scores are available on request.

**Walkthrough.** Open each mode on a fresh profile without scrolling. Find the target, start, make and correct an error, finish a round, improve, continue typing, switch the comparison metric and horizon, inspect exact values, pause and reload. Inspect target, action, result and chart bounds on desktop and mobile, text scaling, keyboard control, reduced motion, storage failure and chart empty, partial and tied cases. A browser walkthrough verifies the presentation and interaction; enjoyment and discoverability with new players need human observation.

## Design evidence

The Infra GUI index, question-first rules, module and screen contracts, visibility priorities, action acknowledgement, chart, web and verification guidance shaped this walkthrough. The September 3 recording calls for presenting relationships visually when this saves the player from scanning and calculating. The August 17 recording ranks actions separately by importance and frequency.

Hornbæk, Kristensson and Oulasvirta, *Introduction to Human–Computer Interaction*, chapters 3, 28 and 41, explain visual attention and grouping, visibility and direct manipulation, and cognitive walkthroughs. The hierarchy here puts the target and frequent action first and places transient feedback at the point of play. The Nielsen Norman Group visual-design poster in the Raspi UX collection informed the use of size and contrast for exceptional records. Yablonski's Flow, Selective Attention and Von Restorff entries in the same collection informed the distinction between ordinary feedback and celebrations. These are design choices for this game. [Open-access HCI textbook](https://introductiontohci.org/) · [Visual design principles](https://www.nngroup.com/articles/principles-visual-design/) · [Selective attention](https://lawsofux.com/selective-attention/)

W3C's status-message guidance supports announcing an outcome while input focus stays in the exercise. Its complex-image guidance supports an accessible text equivalent for a chart. [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) · [Complex images](https://www.w3.org/WAI/tutorials/images/complex/)

## Browser walkthrough results

On a fresh 360 by 780 CSS-pixel viewport, the original Sequence Start button began 1,491 pixels down the document. With the revised layout it begins at 545 and ends at 592. On a 1,280 by 900 desktop viewport it moved from 1,251 to 581. The target and Start fit the first view in every mode at both sizes.

A controlled sequence produced a 1.0-second all-time best, followed by a separate 1.3-second recent best after three slower rounds. At both sizes the gold celebration stayed inside the viewport beside the exercise, clear of the current letter, and keyboard focus remained in the typing input. With reduced motion enabled it appeared without animation. Additional Chromium walkthroughs covered a full 150-letter sequence, enlarged text, keyboard activation, blocked browser storage and a muted celebration. Human enjoyment and physical-device touch keyboard behavior remain unmeasured.
