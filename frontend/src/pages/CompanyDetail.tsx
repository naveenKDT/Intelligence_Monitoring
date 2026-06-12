import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Skeleton,
  Alert,
  Paper,
  TextField,
  CircularProgress,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  Language as WebsiteIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  MonitorHeart as MonitorIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
} from '@mui/icons-material'
import ReactECharts from 'echarts-for-react'

import { companiesApi, dashboardApi, intelligenceApi, monitoringApi } from '../../api/client'

const CompanyDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState(0)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: string; content: string }>>([])

  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', id],
    queryFn: () => companiesApi.get(id!).then((res) => res.data),
    enabled: !!id,
  })

  const { data: dashboardData } = useQuery({
    queryKey: ['dashboard', 'company', id],
    queryFn: () => dashboardApi.getCompany(id!).then((res) => res.data),
    enabled: !!id,
  })

  const { data: chatHistoryData } = useQuery({
    queryKey: ['chat', 'history', id],
    queryFn: () => companiesApi.getChatHistory(id!).then((res) => res.data),
    enabled: !!id,
  })

  const enableMonitoringMutation = useMutation({
    mutationFn: () => monitoringApi.enableMonitoring(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] })
    },
  })

  const disableMonitoringMutation = useMutation({
    mutationFn: () => monitoringApi.disableMonitoring(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] })
    },
  })

  const scrapeMutation = useMutation({
    mutationFn: () => monitoringApi.triggerScrape(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] })
    },
  })

  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      intelligenceApi.chat({ message, company_id: id }),
    onSuccess: (response) => {
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: chatMessage },
        { role: 'assistant', content: response.data.message },
      ])
      setChatMessage('')
    },
  })

  const handleSendChat = () => {
    if (chatMessage.trim()) {
      chatMutation.mutate(chatMessage)
    }
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load company details. The company may not exist.
      </Alert>
    )
  }

  if (isLoading) {
    return (
      <Box>
        <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2, mb: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} />
          </Grid>
          <Grid item xs={12} md={4}>
            <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} />
          </Grid>
        </Grid>
      </Box>
    )
  }

  const aiInsights = dashboardData?.ai_insights || {}

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/companies')}>
          <BackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={600}>
            {company?.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            {company?.industry_classifications?.map((ind: any) => (
              <Chip key={ind.id} label={ind.name} size="small" />
            ))}
            <Chip
              label={company?.status}
              size="small"
              color={company?.is_monitored ? 'warning' : 'default'}
            />
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => scrapeMutation.mutate()}
            disabled={scrapeMutation.isPending}
          >
            {scrapeMutation.isPending ? 'Scraping...' : 'Scrape'}
          </Button>
          {company?.is_monitored ? (
            <Button
              variant="outlined"
              color="error"
              startIcon={<MonitorIcon />}
              onClick={() => disableMonitoringMutation.mutate()}
              disabled={disableMonitoringMutation.isPending}
            >
              Stop Monitoring
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<MonitorIcon />}
              onClick={() => enableMonitoringMutation.mutate()}
              disabled={enableMonitoringMutation.isPending}
            >
              Start Monitoring
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Overview
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                {company?.short_description || company?.description || 'No description available'}
              </Typography>
              
              {company?.business_summary && (
                <>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Business Summary
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {company.business_summary}
                  </Typography>
                </>
              )}

              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary">
                    Headquarters
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {company?.headquarters || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary">
                    Country
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {company?.country || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary">
                    Founded
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {company?.founded_year || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="text.secondary">
                    Employees
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {company?.employee_range || '-'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Tabs */}
          <Card>
            <Tabs
              value={activeTab}
              onChange={(_, v) => setActiveTab(v)}
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab label="Products" />
              <Tab label="Services" />
              <Tab label="Leadership" />
              <Tab label="Locations" />
              <Tab label="News" />
              <Tab label="Documents" />
            </Tabs>

            <CardContent>
              {activeTab === 0 && (
                <List>
                  {company?.products?.map((product: any) => (
                    <ListItem key={product.id} divider>
                      <ListItemText
                        primary={product.name}
                        secondary={
                          <>
                            {product.description && <Typography variant="body2">{product.description}</Typography>}
                            {product.features && (
                              <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {product.features.slice(0, 5).map((f: string, i: number) => (
                                  <Chip key={i} label={f} size="small" variant="outlined" />
                                ))}
                              </Box>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                  {(!company?.products || company.products.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No products available" />
                    </ListItem>
                  )}
                </List>
              )}

              {activeTab === 1 && (
                <List>
                  {company?.services?.map((service: any) => (
                    <ListItem key={service.id} divider>
                      <ListItemText
                        primary={service.name}
                        secondary={service.description || service.category || 'No description'}
                      />
                    </ListItem>
                  ))}
                  {(!company?.services || company.services.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No services available" />
                    </ListItem>
                  )}
                </List>
              )}

              {activeTab === 2 && (
                <List>
                  {company?.leadership?.map((leader: any) => (
                    <ListItem key={leader.id} divider>
                      <ListItemText
                        primary={leader.name}
                        secondary={`${leader.position || ''} ${leader.department ? `• ${leader.department}` : ''}`}
                      />
                    </ListItem>
                  ))}
                  {(!company?.leadership || company.leadership.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No leadership information available" />
                    </ListItem>
                  )}
                </List>
              )}

              {activeTab === 3 && (
                <List>
                  {company?.locations?.map((location: any) => (
                    <ListItem key={location.id} divider>
                      <ListItemText
                        primary={`${location.name || location.location_type || 'Office'} - ${location.city || ''}, ${location.country || ''}`}
                        secondary={location.address}
                      />
                    </ListItem>
                  ))}
                  {(!company?.locations || company.locations.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No location information available" />
                    </ListItem>
                  )}
                </List>
              )}

              {activeTab === 4 && (
                <List>
                  {company?.news?.map((news: any) => (
                    <ListItem key={news.id} divider>
                      <ListItemText
                        primary={news.title}
                        secondary={news.content?.slice(0, 200) || news.source}
                      />
                    </ListItem>
                  ))}
                  {(!company?.news || company.news.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No news available" />
                    </ListItem>
                  )}
                </List>
              )}

              {activeTab === 5 && (
                <List>
                  {company?.documents?.map((doc: any) => (
                    <ListItem key={doc.id} divider>
                      <ListItemText
                        primary={doc.title}
                        secondary={doc.doc_type || doc.description}
                      />
                    </ListItem>
                  ))}
                  {(!company?.documents || company.documents.length === 0) && (
                    <ListItem>
                      <ListItemText secondary="No documents available" />
                    </ListItem>
                  )}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {/* AI Insights */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                AI Insights
              </Typography>
              
              {aiInsights.summary && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Summary
                  </Typography>
                  <Typography variant="body2">
                    {aiInsights.summary}
                  </Typography>
                </Box>
              )}

              {aiInsights.key_strengths?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Key Strengths
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {aiInsights.key_strengths.map((strength: string, i: number) => (
                      <Chip key={i} label={strength} size="small" color="success" variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}

              {aiInsights.industries?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Industries
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {aiInsights.industries.map((ind: string, i: number) => (
                      <Chip key={i} label={ind} size="small" />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Capabilities */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Capabilities
              </Typography>
              {company?.capabilities?.length > 0 ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {company.capabilities.map((cap: string, i: number) => (
                    <Chip key={i} label={cap} size="small" variant="outlined" />
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No capabilities listed
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Chat */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                AI Chat
              </Typography>
              <Box
                sx={{
                  height: 300,
                  overflow: 'auto',
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  p: 2,
                  mb: 2,
                }}
              >
                {chatHistory.map((msg, i) => (
                  <Box
                    key={i}
                    sx={{
                      mb: 1,
                      p: 1,
                      borderRadius: 1,
                      bgcolor: msg.role === 'user' ? 'primary.light' : 'background.paper',
                      color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                    }}
                  >
                    <Typography variant="caption" fontWeight={600}>
                      {msg.role === 'user' ? 'You' : 'AI'}
                    </Typography>
                    <Typography variant="body2">{msg.content}</Typography>
                  </Box>
                ))}
                {chatHistory.length === 0 && (
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    Ask questions about this company
                  </Typography>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  size="small"
                  placeholder="Ask about this company..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
                  fullWidth
                />
                <IconButton
                  color="primary"
                  onClick={handleSendChat}
                  disabled={chatMutation.isPending || !chatMessage.trim()}
                >
                  {chatMutation.isPending ? <CircularProgress size={24} /> : <SendIcon />}
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default CompanyDetail