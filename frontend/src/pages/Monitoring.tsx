import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Skeleton,
  Alert,
  CircularProgress,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
  Notifications as NotificationIcon,
  CloudDownload as ScrapeIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material'
import { monitoringApi, companiesApi } from '../../api/client'

const Monitoring = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState(0)
  const [addUrlDialogOpen, setAddUrlDialogOpen] = useState(false)
  const [newUrl, setNewUrl] = useState('')

  // Fetch scrape queue stats
  const { data: queueStats, isLoading: loadingStats } = useQuery({
    queryKey: ['monitoring', 'scrape-queue', 'stats'],
    queryFn: () => monitoringApi.getScrapeQueueStats().then((res) => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  // Fetch scrape queue items
  const { data: queueItems, isLoading: loadingQueue } = useQuery({
    queryKey: ['monitoring', 'scrape-queue'],
    queryFn: () => monitoringApi.getScrapeQueue({ limit: 50 }).then((res) => res.data),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  // Fetch monitored companies
  const { data: monitoredCompanies, isLoading: loadingCompanies } = useQuery({
    queryKey: ['monitoring', 'companies'],
    queryFn: () => monitoringApi.getMonitoredCompanies(50).then((res) => res.data),
  })

  // Fetch detected changes
  const { data: changes, isLoading: loadingChanges } = useQuery({
    queryKey: ['monitoring', 'changes'],
    queryFn: () => monitoringApi.getChanges({ limit: 50, days: 30 }).then((res) => res.data),
  })

  const disableMutation = useMutation({
    mutationFn: (id: string) => monitoringApi.disableMonitoring(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'companies'] })
    },
  })

  // Add URL to queue mutation
  const addToQueueMutation = useMutation({
    mutationFn: (url: string) => monitoringApi.addToScrapeQueue(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'scrape-queue'] })
      setAddUrlDialogOpen(false)
      setNewUrl('')
    },
  })

  // Clear failed items mutation
  const clearFailedMutation = useMutation({
    mutationFn: () => monitoringApi.clearFailedItems(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'scrape-queue', 'stats'] })
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'scraping': return 'info'
      case 'pending':
      case 'queued': return 'warning'
      case 'failed': return 'error'
      default: return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckIcon fontSize="small" />
      case 'scraping': return <CircularProgress size={16} />
      case 'pending':
      case 'queued': return <PendingIcon fontSize="small" />
      case 'failed': return <ErrorIcon fontSize="small" />
      default: return null
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error'
      case 'high': return 'warning'
      case 'medium': return 'info'
      default: return 'default'
    }
  }

  // Calculate progress percentage
  const totalProcessed = (queueStats?.completed || 0) + (queueStats?.failed || 0)
  const progressPercent = queueStats?.total ? Math.round((totalProcessed / queueStats.total) * 100) : 0

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Monitoring Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        View scraping progress and detected company changes
      </Typography>

      {/* Queue Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScrapeIcon color="primary" />
                <Typography variant="h4" fontWeight={700}>
                  {queueStats?.total || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total in Queue
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PendingIcon color="warning" />
                <Typography variant="h4" fontWeight={700}>
                  {(queueStats?.pending || 0) + (queueStats?.queued || 0)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Ready to Scrape
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckIcon color="success" />
                <Typography variant="h4" fontWeight={700}>
                  {queueStats?.completed || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ErrorIcon color="error" />
                <Typography variant="h4" fontWeight={700}>
                  {queueStats?.failed || 0}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Failed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Progress Bar */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Scraping Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {queueStats?.scraping || 0} currently scraping
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progressPercent} 
            sx={{ height: 10, borderRadius: 5 }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {totalProcessed} processed
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {progressPercent}% complete
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ mb: 3 }}
      >
        <Tab label={`Scrape Queue (${queueItems?.length || 0})`} />
        <Tab label={`Monitored Companies (${monitoredCompanies?.length || 0})`} />
        <Tab label={`Detected Changes (${changes?.length || 0})`} />
      </Tabs>

      {/* Scrape Queue Tab */}
      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 2 }}>
            <Button
              variant="outlined"
              color="error"
              size="small"
              onClick={() => clearFailedMutation.mutate()}
              disabled={clearFailedMutation.isPending || !queueStats?.failed}
            >
              Clear Failed
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddUrlDialogOpen(true)}
            >
              Add URL to Queue
            </Button>
          </Box>

          <Card>
            <CardContent sx={{ p: 0 }}>
              {loadingQueue ? (
                <Box sx={{ p: 3 }}>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height={60} sx={{ mb: 2, borderRadius: 1 }} />
                  ))}
                </Box>
              ) : queueItems?.length > 0 ? (
                <List>
                  {queueItems.map((item: any) => (
                    <ListItem
                      key={item.id}
                      divider
                      secondaryAction={
                        <Chip 
                          icon={getStatusIcon(item.status)} 
                          label={item.status} 
                          color={getStatusColor(item.status) as any}
                          size="small"
                        />
                      }
                    >
                      <ListItemText
                        primary={
                          <Typography variant="body1" sx={{ 
                            maxWidth: '60%', 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {item.url}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Source: {item.source}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Priority: {item.priority}
                            </Typography>
                            {item.retry_count > 0 && (
                              <Typography variant="caption" color="error">
                                Retries: {item.retry_count}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <ScrapeIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No URLs in queue
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Start the scraper service to auto-discover companies, or add URLs manually.
                  </Typography>
                  <Button variant="contained" onClick={() => setAddUrlDialogOpen(true)}>
                    Add URL to Queue
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                How to Start the Scraper
              </Typography>
              <Typography variant="body2" color="text.secondary" component="pre" sx={{ 
                bgcolor: 'grey.100', 
                p: 2, 
                borderRadius: 1,
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap'
              }}>
{`# Run the scraper in a separate terminal:

cd backend
python run_scraper.py

# Or run as background daemon:
python run_scraper.py --daemon

# Check status:
python run_scraper.py --status

# Stop the daemon:
python run_scraper.py --stop`}
              </Typography>
              <Alert severity="info" sx={{ mt: 2 }}>
                The scraper runs as a separate process and continuously discovers and scrapes company websites 24/7. The UI only displays data that has already been scraped.
              </Alert>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Monitored Companies Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          {loadingCompanies ? (
            Array.from({ length: 6 }).map((_, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
              </Grid>
            ))
          ) : monitoredCompanies?.length > 0 ? (
            monitoredCompanies.map((company: any) => (
              <Grid item xs={12} sm={6} md={4} key={company.id}>
                <Card className="dashboard-card">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" fontWeight={600}>
                          {company.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {company.website}
                        </Typography>
                      </Box>
                      <Chip label="Monitoring" color="warning" size="small" />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }} noWrap>
                      {company.short_description || company.description || 'No description'}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      {company.industry_classifications?.slice(0, 2).map((ind: any) => (
                        <Chip key={ind.id} label={ind.name} size="small" variant="outlined" />
                      ))}
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton size="small" onClick={() => navigate(`/companies/${company.id}`)}>
                          <ViewIcon />
                        </IconButton>
                        <IconButton size="small" onClick={() => disableMutation.mutate(company.id)}>
                          <StopIcon />
                        </IconButton>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Last scraped: {company.last_scraped_at ? new Date(company.last_scraped_at).toLocaleDateString() : 'Never'}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Alert severity="info">
                No companies are currently being monitored.{' '}
                <Button onClick={() => navigate('/companies')}>Browse companies</Button> to start monitoring.
              </Alert>
            </Grid>
          )}
        </Grid>
      )}

      {/* Detected Changes Tab */}
      {activeTab === 2 && (
        <Card>
          <CardContent sx={{ p: 0 }}>
            {loadingChanges ? (
              <Box sx={{ p: 3 }}>
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} variant="rectangular" height={60} sx={{ mb: 2, borderRadius: 1 }} />
                ))}
              </Box>
            ) : changes?.length > 0 ? (
              <List>
                {changes.map((change: any, index: number) => (
                  <ListItem
                    key={change.id || index}
                    divider
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/companies/${change.company_id}`)}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1" fontWeight={600}>
                            {change.company?.name || 'Unknown Company'}
                          </Typography>
                          <Chip
                            label={change.change_type.replace(/_/g, ' ')}
                            size="small"
                            color={getSeverityColor(change.severity) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          {change.description}
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            Detected: {new Date(change.detected_at).toLocaleString()}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <NotificationIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No changes detected
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Changes will appear here when monitored companies are updated
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Add URL Dialog */}
      <Dialog open={addUrlDialogOpen} onClose={() => setAddUrlDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add URL to Scrape Queue</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              autoFocus
              fullWidth
              label="Company Website URL"
              placeholder="https://example.com"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              helperText="Enter the URL of a company website to add to the scraping queue"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddUrlDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => addToQueueMutation.mutate(newUrl)}
            disabled={!newUrl || addToQueueMutation.isPending}
          >
            {addToQueueMutation.isPending ? 'Adding...' : 'Add to Queue'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Monitoring