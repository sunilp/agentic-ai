/** Text and step references for the hourglass (hub, Part VI) and the diamond (Step 1). Spec section 4. */
export type Ref = number | string; // numbers are step references, strings are plain text

export const HOURGLASS = {
  above: { title: 'EVERYTHING YOU ANSWER TO', sub: 'EU AI Act · ISO/IEC 42001 · NIST AI RMF · SR 26-2 · board · customers' },
  upper: { title: 'Principles and policy, mapped to one control set', refs: [2, ' · ', 12, ' to ', 16, ' · ', 21] as Ref[] },
  waist: {
    title: 'THE NARROW WAIST',
    lines: ['register · tier · controls', 'evidence pack · platform'],
    refs: [3, ' · ', 4, ' · ', 9, ' · ', 10, ' · ', 20] as Ref[],
  },
  lower: { title: 'Paved road, owners and gates per team', refs: [5, ' to ', 11, ' · ', 19] as Ref[] },
  below: { title: 'EVERY TEAM · SYSTEM · AGENT · BUSINESS UNIT', refs: [17, ' · ', 18, ' · and whatever you build next'] as Ref[] },
  sides: { left: ['rules × teams', 'without a waist'], right: ['rules + teams', 'with one'] },
};

export const DIAMOND = {
  top: 'ACCOUNTABLE · the board',
  bottom: 'ENFORCED · the call',
  bands: [
    { title: 'Policy · principles · tiers', refs: [2, ' · ', 4, ' · ', 12] as Ref[] },
    { title: 'Owners · gates · evidence · the paved road', refs: [6, ' · ', 8, ' · ', 9, ' · ', 10, ' · every team works here'] as Ref[] },
    { title: 'Platform controls · register · gateway', refs: [3, ' · ', 20] as Ref[] },
    { title: 'Model and agent controls', refs: [17, ' · ', 18] as Ref[] },
  ],
  left: ['DIRECTION', 'flows down'],
  right: ['EVIDENCE', 'flows up'],
};

export const refSteps = (refs: Ref[]): number[] => refs.filter((r): r is number => typeof r === 'number');
