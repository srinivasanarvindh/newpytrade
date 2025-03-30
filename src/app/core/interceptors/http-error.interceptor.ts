import {
  HttpRequest,
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export const HttpErrorInterceptor: HttpInterceptorFn = (
  request: HttpRequest<unknown>, 
  next: HttpHandlerFn
): Observable<any> => {
  // Add auth token if available
  const token = localStorage.getItem('token');
  
  if (token) {
    request = request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
  
  // Add withCredentials to enable CORS
  request = request.clone({
    withCredentials: false
  });
  
  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMsg = '';
      
      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMsg = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        if (error.status === 401) {
          // Handle unauthorized errors
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
        
        errorMsg = `Error Code: ${error.status}, Message: ${error.message}`;
      }
      
      console.error(errorMsg);
      return throwError(() => new Error(errorMsg));
    })
  );
}
