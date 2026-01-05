import { useMemo } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { namingConventionsApi, type NamingConvention } from '@/api/clients';

function NamingConventionsTab() {
  const queryClient = useQueryClient();

  const { data: conventions, isLoading, isFetching, error } = useQuery<NamingConvention[]>({
    queryKey: ['naming-conventions'],
    queryFn: namingConventionsApi.getAll,
    placeholderData: [],
  });

  const errorMessage = useMemo(() => {
    if (!error) return null;
    const err = error as any;
    return err?.response?.data?.error ?? (err?.message || 'Failed to load naming conventions');
  }, [error]);

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['naming-conventions'] });
  };

  return (
    <Box sx={{ px: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2} spacing={2}>
        <Typography variant="h6">Naming Conventions</Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isFetching}
          >
            Refresh
          </Button>
        </Stack>
      </Stack>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Conventions are loaded from JSON files in <code>constants/naming_conventions</code>. Assign a
        convention to a client in the Clients tab to drive file validation and discipline mapping.
      </Typography>

      {errorMessage && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Alert>
      )}

      {isLoading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Code</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Standard</TableCell>
                <TableCell align="right">Fields</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {conventions?.map((conv) => (
                <TableRow key={conv.code}>
                  <TableCell>{conv.code}</TableCell>
                  <TableCell>{conv.name}</TableCell>
                  <TableCell>{conv.standard}</TableCell>
                  <TableCell align="right">{conv.field_count}</TableCell>
                </TableRow>
              ))}
              {!conventions?.length && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No naming conventions found. Add JSON files under <code>constants/naming_conventions</code>.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default NamingConventionsTab;
