// components/response/CandidateList.jsx
import React from 'react'
import CandidateCard from './CandidateCard'

const CandidateList = ({ candidates, onCandidateClick }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No candidates found matching the criteria.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {candidates.map((candidate) => (
        <CandidateCard
          key={candidate.ticker}
          rank={candidate.rank}
          ticker={candidate.ticker}
          companyName={candidate.companyName}
          composite={candidate.composite}
          dominantFactor={candidate.dominantFactor}
          dominantFactorValue={candidate.dominantFactorValue}
          selectionReason={candidate.selectionReason}
          factors={candidate.factors}
          onExplore={onCandidateClick}
        />
      ))}
    </div>
  )
}

export default CandidateList
