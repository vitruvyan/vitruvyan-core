// adapters/approvalAdapter.js
// Human approval waiting state adapter
// Created: Jan 18, 2026 - Task 18 Mercator Orchestration

export const approvalAdapter = {
  map(finalState) {
    const approvalStatus = finalState.approval_status || 'pending'
    const autopilotAction = finalState.autopilot_action || {}
    const canResponse = finalState.can_response || {}
    const responseText = finalState.response || canResponse.narrative || ""
    
    // Determine status color and tone
    const statusColorMap = {
      'pending': 'blue',
      'waiting': 'blue',
      'approved': 'green',
      'rejected': 'red',
      'timeout': 'orange',
      'expired': 'orange'
    }
    
    const statusColor = statusColorMap[approvalStatus.toLowerCase()] || 'gray'
    
    const toneMap = {
      'approved': 'success',
      'rejected': 'warning',
      'timeout': 'cautious',
      'expired': 'cautious',
      'pending': 'informative',
      'waiting': 'informative'
    }
    
    const tone = toneMap[approvalStatus.toLowerCase()] || 'neutral'
    
    // Build narrative message based on status
    const narrativeText = responseText || _getApprovalMessage(approvalStatus, autopilotAction)
    
    // Generate contextual follow-ups
    const followUps = canResponse.follow_ups || _generateApprovalFollowUps(approvalStatus)
    
    // Build evidence sections
    const evidenceSections = []
    
    // Section 1: Proposed Action (if available)
    if (autopilotAction && Object.keys(autopilotAction).length > 0) {
      const actionType = autopilotAction.action_type || autopilotAction.action || 'UNKNOWN'
      const ticker = autopilotAction.ticker || 'N/A'
      const quantity = autopilotAction.quantity || autopilotAction.shares || 0
      const price = autopilotAction.price || autopilotAction.limit_price || null
      const reasoning = autopilotAction.reasoning || autopilotAction.rationale || ''
      
      evidenceSections.push({
        id: 'action_preview',
        title: '🎯 Proposed Action',
        priority: 1,
        defaultExpanded: true,
        content: {
          type: 'action_details',
          data: {
            actionType: actionType,
            ticker: ticker,
            quantity: quantity,
            price: price ? `$${price.toFixed(2)}` : 'Market Order',
            estimatedValue: price ? `$${(price * quantity).toFixed(2)}` : 'N/A',
            reasoning: reasoning
          }
        }
      })
    }
    
    // Section 2: Approval Timeline
    const telegramSentAt = finalState.telegram_sent_at || finalState.notification_sent_at
    const approvalExpiresAt = finalState.approval_expires_at
    const approvalReceivedAt = finalState.approval_received_at
    const timeout = finalState.approval_timeout || 300 // 5 minutes default
    
    evidenceSections.push({
      id: 'approval_timeline',
      title: '⏱️ Approval Timeline',
      priority: 2,
      defaultExpanded: approvalStatus === 'pending' || approvalStatus === 'waiting',
      content: {
        type: 'timeline',
        data: {
          status: approvalStatus,
          sentAt: telegramSentAt ? new Date(telegramSentAt).toLocaleTimeString() : 'N/A',
          expiresAt: approvalExpiresAt ? new Date(approvalExpiresAt).toLocaleTimeString() : 'N/A',
          receivedAt: approvalReceivedAt ? new Date(approvalReceivedAt).toLocaleTimeString() : null,
          timeoutSeconds: timeout,
          timeoutFormatted: `${Math.floor(timeout / 60)} minutes`
        }
      }
    })
    
    // Section 3: Safety Checks (if available)
    const safetyChecks = autopilotAction.safety_checks || finalState.safety_checks || []
    if (safetyChecks.length > 0) {
      evidenceSections.push({
        id: 'safety_checks',
        title: '✓ Safety Checks',
        priority: 3,
        defaultExpanded: false,
        content: {
          type: 'checks',
          data: safetyChecks.map(check => ({
            name: check.name || check.check_type || 'Unknown',
            status: check.passed ? 'passed' : 'failed',
            message: check.message || ''
          }))
        }
      })
    }
    
    return {
      narrative: {
        text: narrativeText,
        tone: tone,
        recommendation: null,
        badges: [
          {
            label: approvalStatus.toUpperCase(),
            color: statusColor
          }
        ]
      },
      followUps: followUps,
      context: {
        tickers: autopilotAction.ticker ? [autopilotAction.ticker] : [],
        horizon: null,
        intent: 'approval',
        approvalStatus: approvalStatus,
        conversation_type: 'approval'
      },
      evidence: {
        sections: evidenceSections
      }
    }
  }
}

// Helper: Generate approval message based on status
function _getApprovalMessage(status, action) {
  const actionType = action?.action_type || action?.action || 'action'
  const ticker = action?.ticker || 'position'
  
  const messages = {
    'pending': `⏳ Awaiting your approval for ${actionType} on ${ticker}. Check your Telegram for confirmation.`,
    'waiting': `⏳ Waiting for approval via Telegram. Please respond within the timeout window.`,
    'approved': `✅ Action approved! ${actionType} on ${ticker} will be executed.`,
    'rejected': `❌ Action rejected. ${actionType} on ${ticker} will not be executed.`,
    'timeout': `⏰ Approval timeout expired. ${actionType} on ${ticker} was not executed for safety.`,
    'expired': `⏰ Approval window expired. No action taken for safety reasons.`
  }
  
  return messages[status.toLowerCase()] || `Approval status: ${status}`
}

// Helper: Generate contextual follow-ups based on approval status
function _generateApprovalFollowUps(status) {
  const followUpMap = {
    'pending': [
      "How do I approve in Telegram?",
      "Cancel this action",
      "Show action details"
    ],
    'waiting': [
      "Check approval status",
      "Extend timeout window",
      "Cancel waiting"
    ],
    'approved': [
      "Show execution details",
      "View order status",
      "Analyze impact"
    ],
    'rejected': [
      "Why was it rejected?",
      "Suggest alternative actions",
      "Review safety checks"
    ],
    'timeout': [
      "Retry approval",
      "Adjust timeout settings",
      "Show timeout history"
    ],
    'expired': [
      "Retry action",
      "Configure auto-approval",
      "Review timeout settings"
    ]
  }
  
  return followUpMap[status.toLowerCase()] || [
    "What happened?",
    "Show approval history",
    "Configure approval settings"
  ]
}
