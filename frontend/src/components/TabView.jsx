/**
 * TabView — Clean horizontal tab navigation.
 */
export default function TabView({ tabs = [], activeTab, onTabChange, children }) {
  return (
    <div className="flex flex-col min-h-0">
      {/* Tab bar */}
      <div className="flex items-center gap-6 border-b border-border overflow-x-auto scrollbar-none px-6">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                relative flex items-center gap-2 py-3 text-[13px] font-medium
                whitespace-nowrap transition-colors duration-150 focus:outline-none
                border-b-2 -mb-[1px]
                ${isActive
                  ? 'border-accent text-text-primary'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
                }
              `}
              aria-selected={isActive}
              role="tab"
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count !== null && (
                <span
                  className={`
                    inline-flex items-center justify-center px-1.5 h-[18px]
                    text-[11px] font-medium rounded-full
                    ${tab.dangerCount && tab.count > 0
                        ? 'bg-red/10 text-red'
                        : isActive ? 'bg-bg-elevated text-text-primary' : 'bg-bg-elevated text-text-secondary'
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
      <div className="flex-1 min-h-0 p-6">
        {children}
      </div>
    </div>
  )
}
