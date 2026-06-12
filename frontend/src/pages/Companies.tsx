import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

import { companiesApi } from '../../api/client'

const Companies = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [industry, setIndustry] = useState('')
  const [country, setCountry] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newCompany, setNewCompany] = useState({
    name: '',
    website: '',
    description: '',
    country: '',
    city: '',
  })
  const [notification, setNotification] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['companies', page, pageSize, search, industry, country],
    queryFn: () =>
      companiesApi
        .list({ page, page_size: pageSize, search: search || undefined, industry: industry || undefined, country: country || undefined })
        .then((res) => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => companiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      setCreateDialogOpen(false)
      setNewCompany({ name: '', website: '', description: '', country: '', city: '' })
      setNotification({ open: true, message: 'Company created successfully', severity: 'success' })
    },
    onError: () => {
      setNotification({ open: true, message: 'Failed to create company', severity: 'error' })
    },
  })

  const handleCreateCompany = () => {
    createMutation.mutate(newCompany)
  }

  const columnDefs: ColDef[] = [
    {
      field: 'name',
      headerName: 'Company Name',
      flex: 2,
      cellRenderer: (params: any) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" fontWeight={600}>
            {params.value}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'website',
      headerName: 'Website',
      flex: 1,
      cellRenderer: (params: any) =>
        params.value ? (
          <a href={params.value} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
            {params.value}
          </a>
        ) : (
          '-'
        ),
    },
    {
      field: 'country',
      headerName: 'Country',
      flex: 1,
    },
    {
      field: 'city',
      headerName: 'City',
      flex: 1,
    },
    {
      field: 'status',
      headerName: 'Status',
      flex: 1,
      cellRenderer: (params: any) => (
        <Chip
          label={params.value}
          size="small"
          color={
            params.value === 'active'
              ? 'success'
              : params.value === 'monitoring'
              ? 'warning'
              : 'default'
          }
        />
      ),
    },
    {
      field: 'industry_classifications',
      headerName: 'Industries',
      flex: 1.5,
      cellRenderer: (params: any) =>
        params.value?.map((industry: any) => (
          <Chip key={industry.id} label={industry.name} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
        )),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 1,
      cellRenderer: (params: any) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            size="small"
            onClick={() => navigate(`/companies/${params.data.id}`)}
          >
            <ViewIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ]

  const onGridReady = (params: GridReadyEvent) => {
    params.api.sizeColumnsToFit()
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            Companies
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and monitor company intelligence
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add Company
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              size="small"
              sx={{ minWidth: 300 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              placeholder="Industry"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              size="small"
              sx={{ minWidth: 200 }}
            />
            <TextField
              placeholder="Country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              size="small"
              sx={{ minWidth: 150 }}
            />
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
            >
              Refresh
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Companies Grid */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          <Box className="ag-theme-alpine" sx={{ height: 600, width: '100%' }}>
            <AgGridReact
              rowData={data?.items || []}
              columnDefs={columnDefs}
              onGridReady={onGridReady}
              loading={isLoading}
              pagination={true}
              paginationPageSize={pageSize}
              domLayout="normal"
              defaultColDef={{
                sortable: true,
                resizable: true,
              }}
              onRowClicked={(event) => navigate(`/companies/${event.data.id}`)}
              rowSelection="single"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Pagination Info */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data?.total || 0)} of {data?.total || 0} companies
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <Button
            size="small"
            disabled={page >= (data?.total_pages || 1)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </Box>
      </Box>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Company</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Company Name"
              value={newCompany.name}
              onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Website"
              value={newCompany.website}
              onChange={(e) => setNewCompany({ ...newCompany, website: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={newCompany.description}
              onChange={(e) => setNewCompany({ ...newCompany, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Country"
                value={newCompany.country}
                onChange={(e) => setNewCompany({ ...newCompany, country: e.target.value })}
                fullWidth
              />
              <TextField
                label="City"
                value={newCompany.city}
                onChange={(e) => setNewCompany({ ...newCompany, city: e.target.value })}
                fullWidth
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateCompany}
            disabled={!newCompany.name || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert severity={notification.severity} onClose={() => setNotification({ ...notification, open: false })}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default Companies