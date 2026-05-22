/**
 * TabView — Tabbed navigation component.
 * Props:
 *   tabs: Array<{ id: string, label: string, count?: number }>
 *   activeTab: string
 *   onTabChange: (id: string) => void
 *   children: React node (rendered for active tab)
 */
export default function TabView({ tabs = [], activeTab, onTabChange, children }) {
  return (
    <div className="flex flex-col min-h-0">
      {/* Tab bar */}
      <div className="flex items-end gap-0 border-b border-[#222222] overflow-x-auto scrollbar-none">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                relative flex items-center gap-2 px-5 py-3 text-sm font-medium
                whitespace-nowrap transition-all duration-150 focus:outline-none
                border-b-2 -mb-px
                ${isActive
                  ? 'border-[#00ff88] text-[#00ff88] bg-[rgba(0,255,136,0.04)]'
                  : 'border-transparent text-[#666666] hover:text-[#aaaaaa] hover:border-[#444444] hover:bg-[rgba(255,255,255,0.02)]'
                }
              `}
              aria-selected={isActive}
              role="tab"
            >
              <span className="tracking-wide">{tab.label}</span>
              {tab.count !== undefined && tab.count !== null && (
                <span
                  className={`
                    inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5
                    rounded-full text-[0.6rem] font-bold
                    ${isActive
                      ? tab.danger
                        ? 'bg-[rgba(255,68,68,0.2)] text-[#ff4444]'
                        : 'bg-[rgba(0,255,136,0.15)] text-[#00ff88]'
                      : tab.danger && tab.count > 0
                      ? 'bg-[rgba(255,68,68,0.15)] text-[#ff6666]'
                      : 'bg-[#1e1e1e] text-[#555555]'
                    }
                  `}
                >
                  {tab.count > 999 ? '999+' : tab.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0 animate-fade-in pt-6">
        {children}
      </div>
    </div>
  )
}
