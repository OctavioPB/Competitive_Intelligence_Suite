import { create } from 'zustand'

export interface OutreachPrefill {
  competitor: string
  complaint:  string
  username:   string
}

interface AppStore {
  competitor:        string
  setCompetitor:     (c: string) => void
  demoMode:          boolean
  setDemoMode:       (d: boolean) => void
  outreachPrefill:   OutreachPrefill | null
  setOutreachPrefill:(p: OutreachPrefill | null) => void
}

export const useAppStore = create<AppStore>((set) => ({
  competitor:         'Salesforce',
  setCompetitor:      (competitor)       => set({ competitor }),
  demoMode:           false,
  setDemoMode:        (demoMode)         => set({ demoMode }),
  outreachPrefill:    null,
  setOutreachPrefill: (outreachPrefill)  => set({ outreachPrefill }),
}))
